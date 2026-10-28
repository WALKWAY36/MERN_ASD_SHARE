import math
import subprocess
from typing import Dict, List, Optional, Tuple
from venv import logger
import numpy as np

import json

from pathlib import Path
from scipy.signal import find_peaks

from sklearn.preprocessing import StandardScaler

try:
    # Отключаем CUDA временно для диагностики
    import os

    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

    from ultralytics import YOLO

    YOLO_AVAILABLE = True
    print("YOLO успешно импортирован")
except ImportError as e:
    print(f"YOLO не доступен: {e}")
except OSError as e:
    print(f"Ошибка DLL при импорте YOLO: {e}")
    print("Попытка исправления...")
    # Пробуем альтернативный импорт
    try:
        import sys
        import torch

        print(f"PyTorch version: {torch.__version__}")
        print(f"PyTorch path: {torch.__path__}")
        from ultralytics import YOLO

        YOLO_AVAILABLE = True
    except Exception as e2:
        print(f"Не удалось исправить: {e2}")
        YOLO_AVAILABLE = False

import cv2
from collections import defaultdict
from datetime import datetime
from config.config import MODEL_YOLO_NAME

from utils.histogram_visualizer2 import HistogramVisualizer

import ruptures as rpt


from sklearn.cluster import DBSCAN


# Для видео 30 fps, разрешение 1920x1080:
MIN_CONFIDENCE = 0.6  # Выше = меньше ложных
MAX_REASONABLE_SPEED = 800  # Скорость быстрой руки
MAX_REASONABLE_ACCELERATION = 2000
MIN_TIME_BETWEEN_MOVEMENTS = 0.15  # 150 мс

# Для видео с плохим качеством:
# MIN_CONFIDENCE = 0.4  # Ниже = больше детекций, но больше шума
# MAX_REASONABLE_SPEED = 400  # Строже
# MAX_REASONABLE_ACCELERATION = 1000
# MIN_TIME_BETWEEN_MOVEMENTS = 0.25  # 250 мс


def finalize_video_for_web(input_path, output_path=None):
    """
    Перекодирует видео для корректного веб-стриминга.
    Перемещает moov atom в начало файла (faststart).
    """
    # Конвертируем Path в строку если нужно
    input_path = str(input_path)

    if output_path is None:
        output_path = input_path + ".fixed.mp4"
    else:
        output_path = str(output_path)

    temp_path = input_path + ".temp.mp4"

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-an",
        temp_path,
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        # Заменяем оригинальный файл
        os.replace(temp_path, input_path)
        print(f"Video finalized for web: {input_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False


class MovementAnalyzer:
    """
    Система анализа двигательных паттернов для выявления признаков РАС
    с возможностью экспорта датасета для ML
    """

    def __init__(self, config):
        self.config = config
        self.pose_model = YOLO(MODEL_YOLO_NAME)

        self.movement_stats = defaultdict(list)
        self.progress_callback = None
        self._current_progress = 0

        self.body_parts = {
            0: "нос",
            1: "левый_глаз",
            2: "правый_глаз",
            3: "левое_ухо",
            4: "правое_ухо",
            5: "левое_плечо",
            6: "правое_плечо",
            7: "левый_локоть",
            8: "правый_локоть",
            9: "левое_запястье",
            10: "правое_запястье",
            11: "левое_бедро",
            12: "правое_бедро",
            13: "левое_колено",
            14: "правое_колено",
            15: "левая_лодыжка",
            16: "правая_лодыжка",
        }

        self.critical_parts = [9, 10, 13, 14, 15, 16]

        self.quality_metrics = {
            "total_frames": 0,
            "frames_with_detection": 0,
            "avg_keypoint_confidence": [],
        }

    def set_progress_callback(self, callback):
        """Устанавливает callback для обновления прогресса"""
        self.progress_callback = callback

    def _update_progress(self, progress_value, message=None):
        """Внутренний метод обновления прогресса"""
        self._current_progress = progress_value
        if self.progress_callback:
            try:
                self.progress_callback(progress_value)
            except Exception as e:
                print(f"Progress callback error: {e}")
        if message:
            print(f"[Progress {progress_value}%] {message}")

    def extract_movement_features(
        self, video_path, visualize=False, output_video_path=None
    ):
        """Извлекает признаки движений из видео"""
        self._current_progress = 0
        self.movement_stats.clear()
        self.quality_metrics = {
            "total_frames": 0,
            "frames_with_detection": 0,
            "avg_keypoint_confidence": [],
        }

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = 0
        prev_keypoints = None

        visualizer = None
        video_writer = None
        start_progress = 7
        self._update_progress(start_progress, "start extract_movement_features")
        try:
            if visualize:
                visualizer = HistogramVisualizer(self)
                visualizer.reset_statistics()
                # visualizer = PeakVisualizer(self)
                # visualizer = RealTimeVisualizer(self)

                if output_video_path:
                    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    video_writer = cv2.VideoWriter(
                        output_video_path,
                        fourcc,
                        fps,
                        (width, height),
                    )

            self.quality_metrics["total_frames"] = int(
                cap.get(cv2.CAP_PROP_FRAME_COUNT)
            )

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                results = self.pose_model(frame, verbose=False)[0]

                if results.keypoints is not None and len(results.keypoints.xy) > 0:
                    current_keypoints = results.keypoints.xy[0].cpu().numpy()
                    confidences = (
                        results.keypoints.conf[0].cpu().numpy()
                        if results.keypoints.conf is not None
                        else None
                    )

                    self.quality_metrics["frames_with_detection"] += 1
                    if confidences is not None:
                        self.quality_metrics["avg_keypoint_confidence"].append(
                            np.mean(confidences)
                        )
                    current_abrupt_movements = []
                    if prev_keypoints is not None and len(prev_keypoints) != 0:
                        dt = 1 / fps

                        for part_idx in range(len(current_keypoints)):
                            x_curr, y_curr = current_keypoints[part_idx]
                            x_prev, y_prev = prev_keypoints[part_idx]

                            vx = (x_curr - x_prev) / dt if dt > 0 else 0
                            vy = (y_curr - y_prev) / dt if dt > 0 else 0
                            speed = np.sqrt(vx**2 + vy**2)

                            self.movement_stats[part_idx].append(
                                {
                                    "frame": frame_count,
                                    "time": frame_count / fps,
                                    "x": float(x_curr),
                                    "y": float(y_curr),
                                    "speed": float(speed),
                                    "vx": float(vx),
                                    "vy": float(vy),
                                    "confidence": float(confidences[part_idx])
                                    if confidences is not None
                                    else 1.0,
                                }
                            )

                        # Детектируем пики для текущего кадра
                        for part_idx in self.critical_parts:
                            if part_idx in self.movement_stats:
                                part_data = self.movement_stats[part_idx]
                                if len(part_data) >= 3:  # Нужно минимум 3 точки
                                    # Детектируем пики в реальном времени
                                    peaks = self.detect_abrupt_movements(part_data, fps)

                                    for peak in peaks:
                                        if (
                                            confidences is not None
                                            and confidences[part_idx] < MIN_CONFIDENCE
                                        ):
                                            continue

                                        current_abrupt_movements.append(
                                            {
                                                "part_idx": part_idx,
                                                "time": peak["time"],
                                                "acceleration": peak["acceleration"],
                                                "speed": peak["speed"],
                                            }
                                        )

                    statistics = self.calculate_statistics(fps)

                    if visualize and visualizer:
                        annotated_frame = visualizer.draw_frame(
                            frame=frame,
                            current_keypoints=current_keypoints,
                            confidences=confidences,
                            frame_count=frame_count,
                            fps=fps,
                            prev_keypoints=prev_keypoints,
                            movement_stats=self.movement_stats,
                            current_abrupt_movements=current_abrupt_movements,
                            statistics=statistics,  # ПЕРЕДАЁМ СТАТИСТИКУ
                        )

                        # Показываем окно
                        # cv2.imshow("Movement Analysis - Real Time", annotated_frame)

                        # Сохраняем в видеофайл
                        if video_writer:
                            video_writer.write(annotated_frame)

                        # Управление клавишами
                        key = cv2.waitKey(1) & 0xFF
                        if key == ord("q"):
                            break
                        elif key == ord(" "):  # Пауза
                            while True:
                                key2 = cv2.waitKey(0) & 0xFF
                                if key2 == ord(" "):  # Продолжить
                                    break
                                elif key2 == ord("q"):  # Выход
                                    cap.release()
                                    if video_writer:
                                        video_writer.release()
                                    cv2.destroyAllWindows()
                                    return self.calculate_statistics(fps)

                    prev_keypoints = current_keypoints

                else:
                    statistics = self.calculate_statistics(fps)
                    if visualize and visualizer:
                        annotated_frame = visualizer.draw_frame(
                            frame=frame,
                            current_keypoints=None,
                            confidences=None,
                            frame_count=frame_count,
                            fps=fps,
                            prev_keypoints=None,
                            movement_stats=self.movement_stats,
                            current_abrupt_movements=current_abrupt_movements,
                            statistics=statistics,  # ПЕРЕДАЁМ СТАТИСТИКУ
                        )

                        # cv2.imshow("Movement Analysis - Real Time", annotated_frame)

                        if video_writer:
                            video_writer.write(annotated_frame)

                        key = cv2.waitKey(1) & 0xFF
                        if key == ord("q"):
                            break
                frame_count += 1

                if frame_count % 25 == 0:
                    frame_progress = (
                        frame_count / self.quality_metrics["total_frames"]
                    ) * 90
                    self._update_progress(start_progress + round(frame_progress))
                if frame_count % 100 == 0:
                    print(
                        f"Обработано кадров: {frame_count}/{self.quality_metrics['total_frames']}"
                    )

            cap.release()

            if video_writer:
                video_writer.release()
            if visualize:
                cv2.destroyAllWindows()
        finally:
            if video_writer is not None:
                video_writer.release()
                cv2.destroyAllWindows()
        return self.calculate_statistics(fps)

    def _is_abrupt_now(self, recent_data, fps, threshold=50):
        """Определяет, есть ли резкое движение в последних кадрах"""
        if len(recent_data) < 2:
            return False

        speeds = [d["speed"] for d in recent_data]
        if len(speeds) < 2:
            return False

        # Вычисляем ускорение между последними двумя точками
        dt = 1 / fps
        acceleration = abs((speeds[-1] - speeds[-2]) / dt)

        return acceleration > threshold

    def detect_abrupt_movements(self, part_data, fps, threshold_multiplier=2.5):
        """Детектирует резкие движения"""
        if len(part_data) < 3:
            return []

        speeds = np.array([d["speed"] for d in part_data])
        times = np.array([d["time"] for d in part_data])

        if len(speeds) < 2:
            return []

        dt = 1 / fps
        acceleration = np.diff(speeds) / dt

        mean_acc = np.mean(np.abs(acceleration))
        std_acc = np.std(acceleration)
        threshold = mean_acc + threshold_multiplier * std_acc

        peaks, properties = find_peaks(
            np.abs(acceleration), height=threshold, distance=fps // 2
        )

        abrupt_movements = []
        for peak in peaks:
            data = {
                "time": float(times[peak]),
                "acceleration": float(acceleration[peak]),
                "speed": float(speeds[peak]),
            }

            abrupt_movements.append(data)

        return abrupt_movements

    def calculate_frequency_features(self, part_data, fps):
        """Вычисляет частотные характеристики движений"""
        speeds = np.array([d["speed"] for d in part_data])

        if len(speeds) < 10:  # Минимум 10 точек для FFT
            return {"dominant_frequency_hz": 0.0, "frequency_range_hz": [0.0, 0.0]}

        fft = np.fft.fft(speeds)
        freqs = np.fft.fftfreq(len(speeds), 1 / fps)

        positive_freqs = freqs[: len(freqs) // 2]
        positive_fft = np.abs(fft[: len(fft) // 2])

        if len(positive_freqs) <= 1:
            return {"dominant_frequency_hz": 0.0, "frequency_range_hz": [0.0, 0.0]}

        if len(positive_fft) > 1:
            dominant_freq_idx = np.argmax(positive_fft[1:]) + 1
            dominant_freq = float(positive_freqs[dominant_freq_idx])
        else:
            dominant_freq = 0.0

        energy = positive_fft**2
        total_energy = np.sum(energy)

        if total_energy > 0:
            cumulative_energy = np.cumsum(energy) / total_energy

            idx_5 = np.where(cumulative_energy >= 0.05)[0]
            idx_95 = np.where(cumulative_energy >= 0.95)[0]

            if len(idx_5) > 0 and len(idx_95) > 0:
                freq_range = [
                    float(positive_freqs[idx_5[0]]),
                    float(positive_freqs[idx_95[0]]),
                ]
            else:
                freq_range = [0.0, 0.0]
        else:
            freq_range = [0.0, 0.0]

        return {
            "dominant_frequency_hz": dominant_freq,
            "frequency_range_hz": freq_range,
        }

    def calculate_statistics(self, fps):
        """Вычисляет полную статистику"""
        stats = {
            "total_abrupt_movements": 0,
            "abrupt_movements_by_part": {},
            "movement_frequency": {},
            "symmetry_metrics": {},
            "frequency_features": {},
            "amplitude_features": {},
        }

        for part_idx in self.critical_parts:
            if (
                part_idx in self.movement_stats
                and len(self.movement_stats[part_idx]) > 10
            ):
                part_data = self.movement_stats[part_idx]
                part_name = self.body_parts[part_idx]

                abrupt_moves = self.detect_abrupt_movements(part_data, fps)
                stats["abrupt_movements_by_part"][part_name] = len(abrupt_moves)
                stats["total_abrupt_movements"] += len(abrupt_moves)

                total_time = part_data[-1]["time"] - part_data[0]["time"]
                if total_time > 0:
                    stats["movement_frequency"][part_name] = (
                        len(abrupt_moves) / total_time * 60
                    )

                freq_features = self.calculate_frequency_features(part_data, fps)
                stats["frequency_features"][part_name] = freq_features

                speeds = np.array([d["speed"] for d in part_data])
                stats["amplitude_features"][part_name] = {
                    "mean_speed": float(np.mean(speeds)),
                    "std_speed": float(np.std(speeds)),
                    "max_speed": float(np.max(speeds)),
                    "speed_variance": float(np.var(speeds)),
                }

        left_parts = [9, 13, 15]
        right_parts = [10, 14, 16]

        for l_part, r_part in zip(left_parts, right_parts):
            if l_part in self.movement_stats and r_part in self.movement_stats:
                l_speeds = np.array([d["speed"] for d in self.movement_stats[l_part]])
                r_speeds = np.array([d["speed"] for d in self.movement_stats[r_part]])

                if len(l_speeds) > 0 and len(r_speeds) > 0:
                    min_len = min(len(l_speeds), len(r_speeds))
                    correlation = np.corrcoef(l_speeds[:min_len], r_speeds[:min_len])[
                        0, 1
                    ]

                    pair_name = (
                        f"{self.body_parts[l_part]}_vs_{self.body_parts[r_part]}"
                    )
                    stats["symmetry_metrics"][pair_name] = (
                        1 if math.isnan(float(correlation)) else float(correlation)
                    )

        return stats

    def generate_preliminary_label(self, stats, video_duration):
        """Автоматическая предварительная метка"""
        risk_score = 0
        risk_factors = []

        # 1. Высокая частота резких движений
        movements_per_min = stats["total_abrupt_movements"] / (video_duration / 60)
        if movements_per_min > 15:
            risk_score += 2
            risk_factors.append("high_frequency")

        # 2. Асимметрия
        asymmetry_count = sum(1 for v in stats["symmetry_metrics"].values() if v < 0.5)
        print("asymmetry_count: ", asymmetry_count)
        if asymmetry_count >= 2:
            risk_score += 2
            risk_factors.append("bilateral_asymmetry")

        # 3. Высокая вариабельность
        high_variance = sum(
            1
            for part_features in stats["amplitude_features"].values()
            if part_features.get("speed_variance", 0) > 5000
        )
        if high_variance >= 1:
            risk_score += 1
            risk_factors.append("high_variability")

        return {
            "preliminary_label": 1 if risk_score >= 3 else 0,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
        }

    def save_timeseries(self, output_path):
        """Сохраняет временные ряды для ML"""
        timeseries_data = {}

        for part_idx in self.critical_parts:
            if part_idx in self.movement_stats:
                part_data = self.movement_stats[part_idx]
                part_name = self.body_parts[part_idx]

                timeseries_data[f"{part_name}_x"] = np.array(
                    [d["x"] for d in part_data]
                )
                timeseries_data[f"{part_name}_y"] = np.array(
                    [d["y"] for d in part_data]
                )
                timeseries_data[f"{part_name}_speed"] = np.array(
                    [d["speed"] for d in part_data]
                )
                timeseries_data[f"{part_name}_vx"] = np.array(
                    [d["vx"] for d in part_data]
                )
                timeseries_data[f"{part_name}_vy"] = np.array(
                    [d["vy"] for d in part_data]
                )
                timeseries_data[f"{part_name}_confidence"] = np.array(
                    [d["confidence"] for d in part_data]
                )

        if 9 in self.movement_stats:
            timeseries_data["timestamps"] = np.array(
                [d["time"] for d in self.movement_stats[9]]
            )

        np.savez_compressed(output_path, **timeseries_data)
        print(f"✓ Временные ряды сохранены: {output_path}")

    def export_dataset_sample(self, video_path, output_dir):
        """Экспортирует один образец датасета"""

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        (output_dir / "features").mkdir(parents=True, exist_ok=True)
        (output_dir / "timeseries").mkdir(parents=True, exist_ok=True)
        (output_dir / "videos").mkdir(parents=True, exist_ok=True)

        video_id = Path(video_path).stem

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0
        cap.release()

        print(f"\n{'=' * 60}")
        print(f"Анализ видео: {video_id}")
        print(f"{'=' * 60}")

        video_output_path = output_dir / "videos" / f"{video_id}_analysis.mp4"
        stats = self.extract_movement_features(
            video_path, visualize=True, output_video_path=str(video_output_path)
        )
        self._update_progress(98)
        if os.path.exists(video_output_path):
            finalize_video_for_web(str(video_output_path))
        self._update_progress(99)
        preliminary = self.generate_preliminary_label(stats, duration)

        detection_rate = (
            self.quality_metrics["frames_with_detection"]
            / self.quality_metrics["total_frames"]
        )
        avg_confidence = (
            np.mean(self.quality_metrics["avg_keypoint_confidence"])
            if self.quality_metrics["avg_keypoint_confidence"]
            else 0
        )

        dataset_sample = {
            "video_metadata": {
                "video_id": video_id,
                "duration_sec": float(duration),
                "fps": float(fps),
                "resolution": [width, height],
                "total_frames": total_frames,
                "recording_date": datetime.now().isoformat(),
            },
            "aggregated_features": {
                "total_abrupt_movements": stats["total_abrupt_movements"],
                "movements_per_minute": stats["total_abrupt_movements"]
                / (duration / 60),
                "symmetry_metrics": stats["symmetry_metrics"],
                "frequency_features": stats["frequency_features"],
                "amplitude_features": stats["amplitude_features"],
                "movement_frequency": stats["movement_frequency"],
            },
            "preliminary_annotation": preliminary,
            "quality_metrics": {
                "detection_rate": float(detection_rate),
                "avg_keypoint_confidence": float(avg_confidence),
                "missing_frames": total_frames
                - self.quality_metrics["frames_with_detection"],
            },
            "time_series_summary": {
                "sampling_rate_hz": float(fps),
                "total_samples": len(self.movement_stats.get(9, [])),
            },
        }

        json_path = output_dir / "features" / f"{video_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(dataset_sample, f, indent=2, ensure_ascii=False)
        print(f" Статистика сохранена: {json_path}")

        timeseries_path = output_dir / "timeseries" / f"{video_id}.npz"
        self.save_timeseries(timeseries_path)

        print(f"\n{'=' * 60}")
        print("ПРЕДВАРИТЕЛЬНАЯ ОЦЕНКА")
        print(f"{'=' * 60}")
        print(f"Метка: {preliminary['preliminary_label']} (0=норма, 1=риск)")
        print(
            f"Риск-факторы: {', '.join(preliminary['risk_factors']) if preliminary['risk_factors'] else 'нет'}"
        )
        print(f"Качество трекинга: {detection_rate * 100:.1f}%")

        return dataset_sample

    def extract_motion_signal(self) -> np.ndarray:
        """
        Извлекает сигнал движения из movement_stats.
        Суммирует нормализованные признаки всех частей тела.
        """
        if not self.movement_stats:
            return np.array([])

        # Определяем максимальный номер кадра
        max_frame = 0
        for part_data in self.movement_stats.values():
            if part_data:
                max_frame = max(max_frame, max(d["frame"] for d in part_data))

        n_frames = max_frame + 1

        # Собираем признаки для всех частей тела
        all_features = []

        for part_idx, part_data in self.movement_stats.items():
            if not part_data:
                continue

            # Преобразуем в массивы
            frames = np.array([d["frame"] for d in part_data])
            speeds = np.array([d.get("speed", 0.0) for d in part_data])
            accels = np.array(
                [self._compute_accel(part_data, i) for i in range(len(part_data))]
            )

            # Интерполируем на все кадры
            speed_interp = np.interp(np.arange(n_frames), frames, speeds)
            accel_interp = np.interp(np.arange(n_frames), frames, accels)

            # Нормализуем (Z-score)
            speed_std = speed_interp.std()
            accel_std = accel_interp.std()

            speed_norm = (speed_interp - speed_interp.mean()) / (speed_std + 1e-6)
            accel_norm = (accel_interp - accel_interp.mean()) / (accel_std + 1e-6)

            all_features.append(speed_norm)
            all_features.append(accel_norm)

        if not all_features:
            return np.array([])

        # Суммируем все признаки
        motion_signal = np.sum(all_features, axis=0)

        return motion_signal

    def _compute_accel(self, part_data: List[Dict], idx: int) -> float:
        """Вычисляет ускорение для точки в part_data"""
        if idx == 0 or idx >= len(part_data):
            return 0.0

        dt = part_data[idx]["time"] - part_data[idx - 1]["time"]
        if dt <= 0:
            return 0.0

        dv = part_data[idx]["speed"] - part_data[idx - 1]["speed"]
        return dv / dt

    def segment_with_pelt(
        self, signal: np.ndarray, penalty: Optional[float] = None, model: str = "l2"
    ) -> np.ndarray:
        """
        Сегментирует сигнал методом PELT.

        Args:
            signal: Временной ряд
            penalty: Штраф за точку разрыва (None = авто)
            model: Модель для сегментации

        Returns:
            breakpoints: Индексы точек разрыва
        """
        if len(signal) < 10:
            return np.array([])

        # Автоматический подбор штрафа
        if penalty is None:
            n = len(signal)
            penalty = 2 * np.log(n) * np.std(signal)

        try:
            # Создаем алгоритм PELT
            algo = rpt.Pelt(model=model).fit(signal.reshape(-1, 1))

            # Находим точки разрыва
            breakpoints = algo.predict(pen=penalty)

            return np.array(breakpoints[:-1])  # Убираем последнюю точку
        except Exception as e:
            print(f"⚠ Ошибка в PELT: {e}")
            return np.array([])

    def extract_segment_features(
        self, signal: np.ndarray, breakpoints: np.ndarray
    ) -> np.ndarray:
        """
        Извлекает признаки для каждого сегмента.
        """
        from scipy.stats import skew, kurtosis

        segments = []
        start = 0

        for bp in breakpoints:
            end = bp
            if end > start:
                seg_signal = signal[start:end]

                if len(seg_signal) > 3:
                    features = []

                    # Статистики
                    features.append(np.mean(seg_signal))
                    features.append(np.std(seg_signal))
                    features.append(np.max(seg_signal))
                    features.append(np.min(seg_signal))
                    features.append(np.ptp(seg_signal))

                    # Форма распределения
                    features.append(skew(seg_signal) if len(seg_signal) > 3 else 0)
                    features.append(kurtosis(seg_signal) if len(seg_signal) > 3 else 0)

                    # Энергия
                    features.append(np.sum(seg_signal**2))

                    # Длительность (в секундах)
                    features.append(len(seg_signal) / getattr(self, "fps", 30.0))

                    # Частотные характеристики
                    if len(seg_signal) > 10:
                        fft = np.fft.fft(seg_signal)
                        magnitude = np.abs(fft[: len(fft) // 2])
                        features.append(np.max(magnitude))
                        features.append(
                            np.argmax(magnitude)
                            / len(seg_signal)
                            * getattr(self, "fps", 30.0)
                        )
                    else:
                        features.append(0)
                        features.append(0)

                    segments.append(features)
            start = end

        # Последний сегмент
        if start < len(signal):
            seg_signal = signal[start:]
            if len(seg_signal) > 3:
                features = []
                features.append(np.mean(seg_signal))
                features.append(np.std(seg_signal))
                features.append(np.max(seg_signal))
                features.append(np.min(seg_signal))
                features.append(np.ptp(seg_signal))
                features.append(skew(seg_signal) if len(seg_signal) > 3 else 0)
                features.append(kurtosis(seg_signal) if len(seg_signal) > 3 else 0)
                features.append(np.sum(seg_signal**2))
                features.append(len(seg_signal) / getattr(self, "fps", 30.0))

                if len(seg_signal) > 10:
                    fft = np.fft.fft(seg_signal)
                    magnitude = np.abs(fft[: len(fft) // 2])
                    features.append(np.max(magnitude))
                    features.append(
                        np.argmax(magnitude)
                        / len(seg_signal)
                        * getattr(self, "fps", 30.0)
                    )
                else:
                    features.append(0)
                    features.append(0)

                segments.append(features)

        return np.array(segments)

    def auto_select_dbscan_params(
        self, features: np.ndarray, min_samples_range: Tuple[int, int] = (2, 10)
    ) -> Tuple[float, int]:
        """
        Автоматический подбор параметров DBSCAN.
        """
        if len(features) < 5:
            return 0.5, 2

        from sklearn.neighbors import NearestNeighbors

        # Автоматический выбор MinPts (k)
        n_samples = len(features)
        n_features = features.shape[1]

        # Эвристика из статьи
        k_candidate = min(3, int(np.log(n_samples)))
        k_candidate = min(k_candidate, 2 * n_features + 1)
        min_samples = max(2, k_candidate)

        # Нормализуем признаки
        scaler = StandardScaler()
        features_norm = scaler.fit_transform(features)

        # Ищем оптимальный eps (метод локтя)
        nn = NearestNeighbors(n_neighbors=min_samples)
        nn.fit(features_norm)
        distances, _ = nn.kneighbors(features_norm)
        k_distances = distances[:, -1]
        k_distances_sorted = np.sort(k_distances)

        # Находим точку локтя
        if len(k_distances_sorted) > 2:
            gradients = np.gradient(k_distances_sorted)
            elbow_idx = np.argmax(gradients[: len(gradients) // 2])
            eps = (
                k_distances_sorted[elbow_idx]
                if elbow_idx > 0
                else k_distances_sorted[len(k_distances_sorted) // 3]
            )
        else:
            eps = np.median(k_distances) if len(k_distances) > 0 else 0.5

        return eps, min_samples

    def detect_anomalies(
        self,
        anomaly_threshold: float = 0.3,
        pelt_penalty: Optional[float] = None,
        return_segments: bool = False,
    ) -> Dict:
        """
        Обнаруживает аномальные движения с помощью PELT + DBSCAN.

        Args:
            anomaly_threshold: Кластеры меньше X% от всех считаются аномалиями
            pelt_penalty: Штраф PELT (None = авто)
            return_segments: Возвращать ли все сегменты

        Returns:
            Словарь с результатами
        """
        # 1. Извлекаем сигнал движения
        signal = self.extract_motion_signal()

        if len(signal) < 10:
            return {
                "anomalies": [],
                "normal_segments": [],
                "all_segments": [],
                "cluster_labels": np.array([]),
                "anomaly_ratio": 0.0,
                "n_clusters": 0,
            }

        # 2. Сегментируем PELT
        breakpoints = self.segment_with_pelt(signal, penalty=pelt_penalty)

        if len(breakpoints) == 0:
            return {
                "anomalies": [],
                "normal_segments": [],
                "all_segments": [],
                "cluster_labels": np.array([]),
                "anomaly_ratio": 0.0,
                "n_clusters": 0,
            }

        # 3. Извлекаем признаки сегментов
        segment_features = self.extract_segment_features(signal, breakpoints)

        if len(segment_features) < 3:
            return {
                "anomalies": [],
                "normal_segments": [],
                "all_segments": [],
                "cluster_labels": np.array([]),
                "anomaly_ratio": 0.0,
                "n_clusters": 0,
            }

        # 4. Подбираем параметры DBSCAN
        eps, min_samples = self.auto_select_dbscan_params(segment_features)

        # 5. Кластеризуем
        scaler = StandardScaler()
        features_norm = scaler.fit_transform(segment_features)
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        cluster_labels = dbscan.fit_predict(features_norm)

        # 6. Определяем аномалии
        unique_labels, counts = np.unique(
            cluster_labels[cluster_labels != -1], return_counts=True
        )

        total_segments = len(cluster_labels)
        anomaly_clusters = set()

        for label, count in zip(unique_labels, counts):
            if count / total_segments < anomaly_threshold:
                anomaly_clusters.add(label)

        # 7. Собираем результаты
        anomalies = []
        normal_segments = []
        segment_boundaries = []

        start = 0
        seg_idx = 0
        fps = getattr(self, "fps", 30.0)

        for bp in breakpoints:
            end = bp
            if end > start and seg_idx < len(cluster_labels):
                label = cluster_labels[seg_idx]

                segment_info = {
                    "start_frame": start,
                    "end_frame": end,
                    "duration_sec": (end - start) / fps,
                    "cluster": int(label) if label != -1 else -1,
                    "is_anomaly": label in anomaly_clusters or label == -1,
                }

                if segment_info["is_anomaly"]:
                    anomalies.append(segment_info)
                else:
                    normal_segments.append(segment_info)

                segment_boundaries.append(segment_info)
                seg_idx += 1
            start = end

        # Последний сегмент
        if start < len(signal) and seg_idx < len(cluster_labels):
            label = cluster_labels[seg_idx]
            segment_info = {
                "start_frame": start,
                "end_frame": len(signal),
                "duration_sec": (len(signal) - start) / fps,
                "cluster": int(label) if label != -1 else -1,
                "is_anomaly": label in anomaly_clusters or label == -1,
            }
            if segment_info["is_anomaly"]:
                anomalies.append(segment_info)
            else:
                normal_segments.append(segment_info)
            segment_boundaries.append(segment_info)

        return {
            "anomalies": anomalies,
            "normal_segments": normal_segments,
            "all_segments": segment_boundaries,
            "cluster_labels": cluster_labels,
            "anomaly_ratio": len(anomalies) / max(len(segment_boundaries), 1),
            "dbscan_params": {"eps": eps, "min_samples": min_samples},
            "n_clusters": len(unique_labels),
        }

    def get_anomaly_windows(self, padding_frames: int = 15) -> List[Dict]:
        """
        Возвращает временные окна вокруг аномалий.

        Args:
            padding_frames: Сколько кадров добавить с каждой стороны

        Returns:
            Список окон для анализа
        """
        anomalies_result = self.detect_anomalies()
        fps = getattr(self, "fps", 30.0)

        windows = []
        for anomaly in anomalies_result["anomalies"]:
            start = max(0, anomaly["start_frame"] - padding_frames)
            end = anomaly["end_frame"] + padding_frames

            windows.append(
                {
                    "start_frame": start,
                    "end_frame": end,
                    "center_frame": (anomaly["start_frame"] + anomaly["end_frame"])
                    // 2,
                    "start_time": start / fps,
                    "end_time": end / fps,
                    "duration_sec": anomaly["duration_sec"],
                    "is_anomaly": True,
                }
            )

        return windows
