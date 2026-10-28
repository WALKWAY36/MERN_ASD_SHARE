import cv2
import numpy as np

from utils.realtime_visualizer import RealTimeVisualizer


class PeakVisualizer(RealTimeVisualizer):
    """Визуализатор с выделением пиков прямо на кадре"""

    def __init__(self, analyzer, config=None):
        super().__init__(analyzer, config)

        # Конфигурация пиков
        self.peak_config = {
            "highlight_peak_frames": True,
            "peak_effect_duration": 10,  # кадров
            "peak_color": (0, 0, 255),  # красный
            "peak_radius": 15,
            "show_peak_info": True,
            "recent_peaks": [],  # список последних пиков
        }

        # Эффекты для пиков (для анимации)
        self.active_peaks = []

    def draw_frame(
        self,
        frame,
        current_keypoints,
        confidences,
        frame_count: int,
        fps: float,
        prev_keypoints=None,
        movement_stats=None,
        current_abrupt_movements=None,
    ) -> np.ndarray:
        frame_copy = super().draw_frame(
            frame,
            current_keypoints,
            confidences,
            frame_count,
            fps,
            prev_keypoints,
            movement_stats,
        )

        # Визуализируем пики если есть
        if current_abrupt_movements:
            frame_copy = self._highlight_peaks(
                frame_copy, current_abrupt_movements, current_keypoints, frame_count
            )

        # Обновляем анимации пиков
        frame_copy = self._update_peak_animations(frame_copy, frame_count)

        return frame_copy

    def _highlight_peaks(self, frame, abrupt_movements, keypoints, frame_count):
        """Выделяет пики на видео"""
        for movement in abrupt_movements:
            part_idx = movement.get("part_idx", None)
            time = movement.get("time", 0)
            acceleration = movement.get("acceleration", 0)

            if part_idx is not None and part_idx < len(keypoints):
                x, y = keypoints[part_idx]

                if not np.isnan(x) and not np.isnan(y):
                    point = (int(x), int(y))

                    # Добавляем в список активных пиков для анимации
                    self.active_peaks.append(
                        {
                            "point": point,
                            "start_frame": frame_count,
                            "part_idx": part_idx,
                            "acceleration": acceleration,
                            "radius": self.peak_config["peak_radius"],
                        }
                    )

                    # Рисуем мгновенный эффект
                    self._draw_peak_effect(frame, point, acceleration)

                    # Подписываем значение ускорения
                    if self.peak_config["show_peak_info"]:
                        accel_text = f"PEAK: {abs(acceleration):.0f}"
                        cv2.putText(
                            frame,
                            accel_text,
                            (point[0] + 20, point[1] - 20),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            self.peak_config["peak_color"],
                            2,
                        )

        return frame

    def _draw_peak_effect(self, frame, point, acceleration):
        """Рисует эффект пика (круги, вспышки)"""
        # Концентрические круги
        max_radius = self.peak_config["peak_radius"]
        for radius in range(max_radius, 0, -3):
            alpha = 1.0 - (radius / max_radius)
            color = list(self.peak_config["peak_color"])

            # Прозрачный круг
            overlay = frame.copy()
            cv2.circle(overlay, point, radius, color, 2)
            frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

        # Вспышка в центре
        flash_radius = 8
        overlay = frame.copy()
        cv2.circle(overlay, point, flash_radius, (255, 255, 255), -1)
        frame = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)

        return frame

    def _update_peak_animations(self, frame, frame_count):
        """Обновляет анимации пиков (исчезающие круги)"""
        to_remove = []

        for i, peak in enumerate(self.active_peaks):
            elapsed = frame_count - peak["start_frame"]

            if elapsed < self.peak_config["peak_effect_duration"]:
                # Вычисляем альфа-канал для исчезновения
                alpha = 1.0 - (elapsed / self.peak_config["peak_effect_duration"])

                # Рисуем исчезающий круг
                radius = int(peak["radius"] * alpha)
                if radius > 0:
                    color = list(self.peak_config["peak_color"])
                    overlay = frame.copy()
                    cv2.circle(overlay, peak["point"], radius, color, 2)
                    frame = cv2.addWeighted(
                        overlay, alpha * 0.5, frame, 1 - alpha * 0.5, 0
                    )
            else:
                to_remove.append(i)

        # Удаляем старые пики
        for i in reversed(to_remove):
            self.active_peaks.pop(i)

        return frame

    def _draw_peak_counter(self, frame, total_peaks, frame_count, fps):
        """Счетчик пиков в углу экрана"""
        h, w = frame.shape[:2]

        # Панель счетчика
        counter_width = 150
        counter_height = 40
        counter_x = w - counter_width - 10
        counter_y = 50

        # Фон
        cv2.rectangle(
            frame,
            (counter_x, counter_y),
            (counter_x + counter_width, counter_y + counter_height),
            (40, 40, 40),
            -1,
        )
        cv2.rectangle(
            frame,
            (counter_x, counter_y),
            (counter_x + counter_width, counter_y + counter_height),
            (100, 100, 100),
            1,
        )

        # Текст
        peaks_text = f"ABRUPT MOVEMENTS: {total_peaks}"
        cv2.putText(
            frame,
            peaks_text,
            (counter_x + 10, counter_y + 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            self.peak_config["peak_color"],
            1,
        )

        # Частота пиков в минуту
        time_min = (frame_count / fps) / 60 if fps > 0 else 0
        if time_min > 0:
            rate = total_peaks / time_min
            rate_text = f"Rate: {rate:.1f}/min"
            cv2.putText(
                frame,
                rate_text,
                (counter_x + 10, counter_y + 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (200, 200, 200),
                1,
            )

        return frame
