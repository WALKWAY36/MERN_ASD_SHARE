import cv2
import numpy as np
from typing import Optional, Dict, List, Tuple
import math
from PIL import Image, ImageDraw, ImageFont
import io


class RealTimeVisualizer:
    """Визуализатор для отображения анализа в реальном времени"""

    def __init__(self, analyzer, config=None):
        """
        Args:
            analyzer: Экземпляр MovementAnalyzer
            config: Конфигурация визуализации
        """
        self.analyzer = analyzer

        # Конфигурация по умолчанию
        self.config = config or {
            "show_skeleton": True,
            "show_keypoints": True,
            "show_stats": True,
            "show_movement_vectors": True,
            "tracking_history_length": 30,
            "use_pil_for_text": False,  # True для русского текста (медленнее)
            "colors": {
                "skeleton": (0, 165, 255),
                "left_side": (0, 165, 255),
                "right_side": (0, 165, 255),
                "critical_part": (0, 165, 255),
                "text": (255, 255, 255),  # BGR - белый
                "background": (50, 50, 50),  # BGR - тёмно-серый
                "vector": (255, 255, 0),  # BGR - голубой
                "warning": (0, 0, 255),  # BGR - красный для предупреждений
                "info": (0, 255, 255),  # BGR - жёлтый для информации
            },
            "thickness": {
                "skeleton": 2,
                "keypoint": 4,
                "vector": 1,
                "text": 1,
            },
        }

        # Пытаемся загрузить шрифт для PIL
        if self.config["use_pil_for_text"]:
            try:
                self.pil_font = ImageFont.truetype("arial.ttf", 16)
                self.pil_font_small = ImageFont.truetype("arial.ttf", 12)
            except:
                print("⚠️ Шрифт не найден, используем стандартный")
                self.pil_font = ImageFont.load_default()
                self.pil_font_small = ImageFont.load_default()

        # Определим связи для скелета
        self.skeleton_connections = [
            (5, 7),
            (7, 9),  # Левая рука
            (6, 8),
            (8, 10),  # Правая рука
            (5, 6),  # Плечи
            (5, 11),
            (6, 12),  # Туловище
            (11, 13),
            (13, 15),  # Левая нога
            (12, 14),
            (14, 16),  # Правая нога
            (11, 12),  # Бёдра
            (0, 1),
            (0, 2),  # Лицо
            (1, 3),
            (2, 4),
        ]

        # Английские названия для частей тела (чтобы не было проблем с кодировкой)
        self.body_parts_en = {
            0: "nose",
            1: "L_eye",
            2: "R_eye",
            3: "L_ear",
            4: "R_ear",
            5: "L_shoulder",
            6: "R_shoulder",
            7: "L_elbow",
            8: "R_elbow",
            9: "L_wrist",
            10: "R_wrist",
            11: "L_hip",
            12: "R_hip",
            13: "L_knee",
            14: "R_knee",
            15: "L_ankle",
            16: "R_ankle",
        }

    def _put_text_rus(
        self, frame, text, position, font_scale=0.5, color=(255, 255, 255), thickness=1
    ):
        """Вспомогательная функция для русского текста через PIL"""
        if not self.config["use_pil_for_text"]:
            # Используем только ASCII символы
            ascii_text = text.encode("ascii", "ignore").decode("ascii")
            if not ascii_text:
                ascii_text = "???"
            cv2.putText(
                frame,
                ascii_text,
                position,
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                color,
                thickness,
            )
            return frame

        # Конвертируем кадр OpenCV в PIL
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)

        # Рисуем текст
        draw.text(
            position,
            text,
            font=self.pil_font_small,
            fill=(color[2], color[1], color[0]),
        )  # RGB -> BGR

        # Конвертируем обратно
        frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        return frame

    def draw_frame(
        self,
        frame,
        current_keypoints,
        confidences,
        frame_count: int,
        fps: float,
        prev_keypoints=None,
        movement_stats=None,
    ) -> np.ndarray:
        """
        Основной метод отрисовки анализа на кадре
        """
        frame_copy = frame.copy()

        # Проверяем валидность ключевых точек
        if current_keypoints is None or len(current_keypoints) == 0:
            return self._draw_no_detection(frame_copy)

        # 1. Отрисовка скелета и ключевых точек
        if self.config["show_skeleton"]:
            frame_copy = self._draw_skeleton(frame_copy, current_keypoints, confidences)

        # 2. Отрисовка векторов движения
        if self.config["show_movement_vectors"] and prev_keypoints is not None:
            frame_copy = self._draw_movement_vectors(
                frame_copy, current_keypoints, prev_keypoints, fps
            )

        # 3. Отрисовка статистики
        if self.config["show_stats"]:
            frame_copy = self._draw_realtime_stats(
                frame_copy, movement_stats, frame_count, fps
            )

        # 4. Добавляем информационный заголовок
        frame_copy = self._draw_info_header(frame_copy, frame_count, fps)

        return frame_copy

    def _draw_no_detection(self, frame: np.ndarray) -> np.ndarray:
        """Отрисовка при отсутствии детекции"""
        height, width = frame.shape[:2]

        # Полупрозрачный overlay
        overlay = frame.copy()
        cv2.rectangle(
            overlay, (0, 0), (width, height), self.config["colors"]["background"], -1
        )
        frame = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)

        # Текст предупреждения (только ASCII)
        text = "NO POSE DETECTION"
        font_scale = 1.5
        thickness = 3
        color = self.config["colors"]["warning"]

        text_size = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
        )[0]
        text_x = (width - text_size[0]) // 2
        text_y = (height + text_size[1]) // 2

        cv2.putText(
            frame,
            text,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            color,
            thickness,
        )

        return frame

    def _draw_skeleton(
        self,
        frame: np.ndarray,
        keypoints: np.ndarray,
        confidences: Optional[np.ndarray],
    ) -> np.ndarray:
        """Отрисовка скелета и ключевых точек с проверкой пропущенных точек"""
        # Список для отслеживания видимых точек

        visible_points = set()

        # Сначала отмечаем видимые точки
        for i, (x, y) in enumerate(keypoints):
            if (
                x != 0
                and y != 0
                and not np.isnan(x)
                and not np.isnan(y)
                and (
                    confidences is None
                    or (i < len(confidences) and confidences[i] > 0.3)
                )
            ):
                visible_points.add(i)

        # Теперь рисуем только связи между видимыми точками
        for start_idx, end_idx in self.skeleton_connections:
            if start_idx in visible_points and end_idx in visible_points:
                start_x, start_y = keypoints[start_idx]
                end_x, end_y = keypoints[end_idx]

                start_pt = (int(start_x), int(start_y))
                end_pt = (int(end_x), int(end_y))

                # Определяем цвет
                if start_idx in [5, 7, 9, 11, 13, 15]:
                    color = self.config["colors"]["left_side"]
                elif start_idx in [6, 8, 10, 12, 14, 16]:
                    color = self.config["colors"]["right_side"]
                else:
                    color = self.config["colors"]["skeleton"]

                cv2.line(
                    frame, start_pt, end_pt, color, self.config["thickness"]["skeleton"]
                )

        # Рисуем видимые точки
        for i in visible_points:
            x, y = keypoints[i]
            point = (int(x), int(y))

            if i in self.analyzer.critical_parts:
                color = self.config["colors"]["critical_part"]
                radius = 6
            elif i in [5, 6, 7, 8, 9, 10]:
                color = (255, 255, 0)
                radius = 4
            else:
                color = (0, 255, 255)
                radius = 3

            cv2.circle(frame, point, radius, color, -1)

        return frame

    def _draw_movement_vectors(
        self, frame: np.ndarray, current_kp: np.ndarray, prev_kp: np.ndarray, fps: float
    ) -> np.ndarray:
        """Отрисовка векторов движения"""
        if fps <= 0:
            return frame

        dt = 1.0 / fps
        color = self.config["colors"]["vector"]
        thickness = self.config["thickness"]["vector"]

        for part_idx in self.analyzer.critical_parts:
            if (
                part_idx < len(current_kp)
                and part_idx < len(prev_kp)
                and not (
                    np.isnan(current_kp[part_idx][0]) or np.isnan(prev_kp[part_idx][0])
                )
            ):
                x_curr, y_curr = current_kp[part_idx]
                x_prev, y_prev = prev_kp[part_idx]

                # Вычисляем смещение
                dx = x_curr - x_prev
                dy = y_curr - y_prev

                # Пропускаем слишком маленькие движения
                if abs(dx) < 0.5 and abs(dy) < 0.5:
                    continue

                # Масштабируем для лучшей видимости
                scale = 2.0
                dx_scaled = dx * scale
                dy_scaled = dy * scale

                # Начальная и конечная точки вектора
                start_pt = (int(x_prev), int(y_prev))
                end_pt = (int(x_prev + dx_scaled), int(y_prev + dy_scaled))

                # Рисуем вектор
                cv2.arrowedLine(
                    frame, start_pt, end_pt, color, thickness, tipLength=0.3
                )

                # Вычисляем скорость
                speed = np.sqrt(dx**2 + dy**2) / dt

                # Цвет текста в зависимости от скорости
                if speed > 100:  # Порог для "быстрого" движения
                    speed_color = (0, 0, 255)  # Красный
                else:
                    speed_color = color

                # Текст скорости (ASCII только)
                speed_text = f"{speed:.0f}"
                text_pos = (end_pt[0] + 5, end_pt[1] - 5)
                cv2.putText(
                    frame,
                    speed_text,
                    text_pos,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    speed_color,
                    1,
                )

        return frame

    def _draw_realtime_stats(
        self, frame: np.ndarray, movement_stats: Dict, frame_count: int, fps: float
    ) -> np.ndarray:
        """Отрисовка статистики в реальном времени"""
        if not movement_stats:
            return frame

        height, width = frame.shape[:2]
        color = self.config["colors"]["text"]
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Создаем панель статистики
        panel_width = 250
        panel_height = 180
        panel_x = width - panel_width - 10
        panel_y = 10

        # Полупрозрачный фон панели
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (40, 40, 40),
            -1,
        )
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)

        # Заголовок панели (ASCII)
        title = "REAL-TIME STATS"
        cv2.putText(frame, title, (panel_x + 10, panel_y + 20), font, 0.5, color, 1)

        # Разделительная линия
        cv2.line(
            frame,
            (panel_x, panel_y + 30),
            (panel_x + panel_width, panel_y + 30),
            color,
            1,
        )

        y_offset = 45
        line_height = 18

        # Статистика для критических частей тела
        for part_idx in self.analyzer.critical_parts:
            if part_idx in movement_stats and movement_stats[part_idx]:
                part_data = movement_stats[part_idx]

                if len(part_data) > 0:
                    speeds = [d["speed"] for d in part_data]
                    # dt = 1 / fps
                    # acceleration = np.diff(speeds) / dt
                    # max_acc = np.max(np.abs(acceleration))

                    if speeds:
                        current_speed = speeds[-1]
                        avg_speed = np.mean(speeds)
                        max_speed = np.max(speeds) if len(speeds) > 1 else current_speed

                        # Используем английские названия
                        part_name = self.body_parts_en[part_idx]

                        # Форматируем строку
                        stats_text = f"{part_name:12s}: {current_speed:5.0f}"

                        # Цвет в зависимости от скорости
                        text_color = color
                        if current_speed > 150:  # Высокая скорость
                            text_color = (0, 0, 255)  # Красный
                        elif current_speed > 80:  # Средняя скорость
                            text_color = (0, 165, 255)  # Оранжевый

                        cv2.putText(
                            frame,
                            stats_text,
                            (panel_x + 10, panel_y + y_offset),
                            font,
                            0.4,
                            text_color,
                            1,
                        )

                        # Дополнительная строка: средняя/максимальная
                        if y_offset + line_height < panel_height - 20:
                            extra_text = f"  avg:{avg_speed:4.0f} max:{max_speed:4.0f} "
                            cv2.putText(
                                frame,
                                extra_text,
                                (panel_x + 10, panel_y + y_offset + 10),
                                font,
                                0.35,
                                (150, 150, 150),
                                1,
                            )

                        y_offset += line_height + 5

        # Информация о времени
        time_sec = frame_count / fps if fps > 0 else 0
        time_text = f"Time: {time_sec:.1f}s | Frame: {frame_count}"
        cv2.putText(
            frame,
            time_text,
            (panel_x + 10, panel_y + panel_height - 10),
            font,
            0.4,
            color,
            1,
        )

        return frame

    def _draw_info_header(
        self, frame: np.ndarray, frame_count: int, fps: float
    ) -> np.ndarray:
        """Отрисовка информационного заголовка (только ASCII)"""
        height, width = frame.shape[:2]

        # Полупрозрачная верхняя панель
        header_height = 40
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, header_height), (30, 30, 30), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

        # Заголовок (ASCII)
        title = ""  # "MOVEMENT PATTERN ANALYSIS - REAL TIME"
        title_size = cv2.getTextSize(title, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        title_x = (width - title_size[0]) // 2

        cv2.putText(
            frame,
            title,
            (title_x, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        # Левая часть: информация о кадрах
        left_info = f"Frame: {frame_count} | FPS: {fps:.1f}"
        cv2.putText(
            frame,
            left_info,
            (10, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1,
        )

        # Правая часть: горячие клавиши
        right_info = "Q: quit | SPACE: pause | S: save frame"
        right_size = cv2.getTextSize(right_info, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        cv2.putText(
            frame,
            right_info,
            (width - right_size[0] - 10, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1,
        )

        return frame

    def draw_simple_text(
        self,
        frame: np.ndarray,
        text: str,
        position: Tuple[int, int],
        font_scale: float = 0.7,
        color: Tuple[int, int, int] = (255, 255, 255),
        thickness: int = 2,
    ) -> np.ndarray:
        """
        Универсальный метод для рисования текста с обработкой русских символов
        """
        # Если в тексте есть не-ASCII символы
        try:
            text.encode("ascii")
            # Все символы ASCII - можно использовать cv2.putText
            cv2.putText(
                frame,
                text,
                position,
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                color,
                thickness,
            )
        except UnicodeEncodeError:
            # Есть русские символы
            if self.config["use_pil_for_text"]:
                return self._put_text_rus(
                    frame, text, position, font_scale, color, thickness
                )
            else:
                # Заменяем русский текст на английский или удаляем
                ascii_text = text.encode("ascii", "ignore").decode("ascii")
                if ascii_text:
                    cv2.putText(
                        frame,
                        ascii_text,
                        position,
                        cv2.FONT_HERSHEY_SIMPLEX,
                        font_scale,
                        color,
                        thickness,
                    )

        return frame
