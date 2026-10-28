import os

import matplotlib
from utils.realtime_visualizer import RealTimeVisualizer

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import numpy as np
import cv2
from collections import defaultdict, deque
import math

matplotlib.use("Agg")
os.environ["QT_QPA_PLATFORM"] = "offscreen"


class HistogramVisualizer(RealTimeVisualizer):
    """Визуализатор со статистикой резких движений по частям тела"""

    def __init__(self, analyzer, config=None):
        if hasattr(self, "movement_stats"):
            self.movement_stats = {}
        if hasattr(self, "peaks_history"):
            self.peaks_history = []
        if hasattr(self, "time_bins"):
            self.time_bins = defaultdict(int)
        super().__init__(analyzer, config)

        # КРИТИЧЕСКИЕ ЧАСТИ ТЕЛА (только то, что нужно)
        self.critical_parts = {
            4: "Right Wrist",  # Правое запястье
            7: "Left Wrist",  # Левое запястье
            10: "Right Knee",  # Правое колено
            13: "Left Knee",  # Левое колено
            11: "Right Ankle",  # Правая лодыжка
            14: "Left Ankle",  # Левая лодыжка
        }

        # Цвета для каждой части
        self.part_colors = {
            4: (0, 200, 255),  # Right Wrist - жёлтый
            7: (255, 200, 0),  # Left Wrist - голубой
            10: (0, 100, 255),  # Right Knee - оранжевый
            13: (255, 100, 0),  # Left Knee - синий
            11: (0, 255, 100),  # Right Ankle - зелёный
            14: (255, 0, 255),  # Left Ankle - розовый
        }

        # Счётчики для критических частей
        self.part_counters = {part_id: 0 for part_id in self.critical_parts.keys()}
        self.part_last_minute = {part_id: 0 for part_id in self.critical_parts.keys()}
        self.part_history = {
            part_id: deque(maxlen=100) for part_id in self.critical_parts.keys()
        }

        # Общая статистика
        self.total_movements = 0
        self.last_minute_total = 0

        # Для хранения времени последних движений
        self.movement_times = deque(maxlen=100)

        # Список последних движений для отображения
        self.recent_movements = deque(maxlen=10)

        self.reset_statistics()

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
        statistics=None,  # НОВЫЙ ПАРАМЕТР
    ) -> np.ndarray:
        """
        Отрисовка со статистикой резких движений
        """
        # print(statistics)
        frame_copy = super().draw_frame(
            frame,
            current_keypoints,
            confidences,
            frame_count,
            fps,
            prev_keypoints,
            movement_stats,
        )

        # Если передана готовая статистика - используем её
        if statistics:
            self._update_from_statistics(
                statistics, current_abrupt_movements, frame_count, fps
            )
        else:
            # Иначе обновляем статистику при резких движениях (старое поведение)
            if current_abrupt_movements:
                self._update_statistics(current_abrupt_movements, frame_count, fps)

        # Визуализируем резкие движения
        if current_abrupt_movements:
            frame_copy = self._visualize_movements(
                frame_copy, current_abrupt_movements, current_keypoints
            )

        # Рисуем основную панель статистики
        frame_copy = self._draw_statistics_panel(frame_copy, frame_count, fps)

        # Рисуем лог последних движений
        frame_copy = self._draw_movement_log(frame_copy)

        # Рисуем скелет с подсветкой активных частей
        frame_copy = self._draw_skeleton_with_highlights(
            frame_copy, current_keypoints, confidences, current_abrupt_movements
        )

        return frame_copy

    def _update_from_statistics(self, statistics, abrupt_movements, frame_count, fps):
        """Обновляет визуализатор из готовой статистики"""

        # МАППИНГ русских названий на ID частей тела
        russian_to_id = {
            "левое_запястье": 7,
            "правое_запястье": 4,
            "левое_колено": 13,
            "правое_колено": 10,
            "левая_лодыжка": 14,
            "правая_лодыжка": 11,
        }

        # 1. Обновляем общую статистику
        # Используем total_abrupt_movements вместо total_movements
        if "total_abrupt_movements" in statistics:
            self.total_movements = statistics["total_abrupt_movements"]
        else:
            self.total_movements = statistics.get("total_movements", 0)

        # 2. Обновляем статистику по частям тела
        abrupt_by_part = statistics.get("abrupt_movements_by_part", {})

        for russian_name, count in abrupt_by_part.items():
            part_id = russian_to_id.get(russian_name)
            if part_id is not None and part_id in self.part_counters:
                self.part_counters[part_id] = count

        # 3. Вычисляем last_minute_total из частей (или используем другое поле)
        self.last_minute_total = sum(self.part_last_minute.values())

        # 4. Обновляем last_minute для каждой части (если есть данные)
        # Если в статистике нет last_minute, оставляем текущие значения

        # 5. Обрабатываем резкие движения для лога
        current_time = frame_count / fps if fps > 0 else 0
        if abrupt_movements:
            for movement in abrupt_movements:
                part_idx = movement.get("part_idx", -1)
                acceleration = movement.get("acceleration", 0)

                if part_idx in self.critical_parts:
                    intensity = min(10, int(abs(acceleration) / 100))
                    self.recent_movements.append(
                        {
                            "time": current_time,
                            "part": self.critical_parts[part_idx],
                            "intensity": intensity,
                            "acceleration": acceleration,
                        }
                    )

    def _visualize_movements(self, frame, abrupt_movements, current_keypoints):
        """Визуализирует резкие движения на теле"""
        if current_keypoints is None:
            return frame

        for movement in abrupt_movements:
            part_idx = movement.get("part_idx", -1)
            acceleration = movement.get("acceleration", 0)

            if part_idx not in self.critical_parts:
                continue

            if (
                part_idx < len(current_keypoints)
                and current_keypoints[part_idx] is not None
            ):
                x, y = current_keypoints[part_idx]
                if x > 0 and y > 0:
                    x, y = int(x), int(y)

                    # Интенсивность движения
                    intensity = min(10, int(abs(acceleration) / 100))

                    # Размер эффекта зависит от интенсивности
                    radius = 20 + intensity * 3

                    # Пульсирующий круг
                    pulse = (
                        radius + int(5 * math.sin(math.time() * 20))
                        if hasattr(math, "time")
                        else radius
                    )
                    cv2.circle(frame, (x, y), pulse, (0, 0, 255), 3)
                    cv2.circle(frame, (x, y), pulse - 5, (0, 255, 255), 2)

                    # Текст с интенсивностью
                    cv2.putText(
                        frame,
                        f"!{intensity}",
                        (x - 15, y - 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 0, 255),
                        2,
                    )

        return frame

    def _draw_skeleton_with_highlights(
        self, frame, keypoints, confidences, abrupt_movements
    ):
        """Рисует скелет с подсветкой активных частей"""
        if keypoints is None:
            return frame

        # Активные части в этом кадре
        active_parts = set()
        if abrupt_movements:
            for m in abrupt_movements:
                active_parts.add(m.get("part_idx", -1))

        # Рисуем соединения
        connections = [
            (5, 6),
            (5, 7),
            (7, 9),
            (6, 8),
            (8, 10),  # Руки
            (5, 11),
            (6, 12),
            (11, 12),  # Тело
            (11, 13),
            (13, 15),
            (12, 14),
            (14, 16),  # Ноги
        ]

        for conn in connections:
            if conn[0] < len(keypoints) and conn[1] < len(keypoints):
                x1, y1 = keypoints[conn[0]]
                x2, y2 = keypoints[conn[1]]
                if x1 > 0 and y1 > 0 and x2 > 0 and y2 > 0:
                    # Цвет соединения зависит от активности
                    if conn[0] in active_parts or conn[1] in active_parts:
                        color = (0, 0, 255)  # Красный для активных
                        thickness = 3
                    else:
                        color = (100, 100, 100)  # Серый для неактивных
                        thickness = 2
                    cv2.line(
                        frame, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness
                    )

        # Рисуем ключевые точки
        for i, (x, y) in enumerate(keypoints):
            if x > 0 and y > 0 and i in self.critical_parts:
                # Критические точки
                if i in active_parts:
                    color = (0, 0, 255)  # Красный - активное движение
                    radius = 10
                else:
                    # Цвет в зависимости от общего количества движений
                    total = self.part_counters.get(i, 0)
                    if total > 20:
                        color = (0, 0, 255)  # Красный - много движений
                    elif total > 10:
                        color = (0, 165, 255)  # Оранжевый - среднее
                    else:
                        color = self.part_colors.get(
                            i, (0, 255, 0)
                        )  # Цвет по умолчанию
                    radius = 8

                cv2.circle(frame, (int(x), int(y)), radius, color, -1)
                cv2.circle(frame, (int(x), int(y)), radius + 2, (255, 255, 255), 2)

                # Текст с количеством движений
                cv2.putText(
                    frame,
                    str(self.part_counters.get(i, 0)),
                    (int(x) - 8, int(y) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    2,
                )

        return frame

    def _draw_statistics_panel(self, frame, frame_count, fps):
        """Рисует главную панель статистики"""
        h, w = frame.shape[:2]

        # Панель статистики (левый верхний угол)
        panel_x, panel_y = 10, 50
        panel_w, panel_h = 320, 280

        # Фон
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (panel_x, panel_y),
            (panel_x + panel_w, panel_y + panel_h),
            (0, 0, 0),
            -1,
        )
        frame = cv2.addWeighted(overlay, 0.85, frame, 0.15, 0)
        cv2.rectangle(
            frame,
            (panel_x, panel_y),
            (panel_x + panel_w, panel_y + panel_h),
            (0, 200, 255),
            2,
        )

        # Заголовок
        cv2.putText(
            frame,
            "ABRUPT MOVEMENTS STATISTICS",
            (panel_x + 10, panel_y + 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 200, 255),
            1,
        )

        # Разделитель
        cv2.line(
            frame,
            (panel_x, panel_y + 35),
            (panel_x + panel_w, panel_y + 35),
            (100, 100, 100),
            1,
        )

        # Общая статистика
        cv2.putText(
            frame,
            f"TOTAL: {self.total_movements}",
            (panel_x + 10, panel_y + 55),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            f"LAST MINUTE: {self.last_minute_total}",
            (panel_x + 10, panel_y + 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0)
            if self.last_minute_total < 20
            else (0, 165, 255)
            if self.last_minute_total < 40
            else (0, 0, 255),
            1,
        )

        # Разделитель
        cv2.line(
            frame,
            (panel_x, panel_y + 85),
            (panel_x + panel_w, panel_y + 85),
            (100, 100, 100),
            1,
        )

        # Заголовок таблицы
        cv2.putText(
            frame,
            "BODY PART",
            (panel_x + 10, panel_y + 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (200, 200, 200),
            1,
        )
        cv2.putText(
            frame,
            "TOTAL",
            (panel_x + 160, panel_y + 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (200, 200, 200),
            1,
        )
        cv2.putText(
            frame,
            "LAST MIN",
            (panel_x + 230, panel_y + 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (200, 200, 200),
            1,
        )

        # Статистика по каждой части
        y_offset = panel_y + 125
        for part_id, part_name in self.critical_parts.items():
            total = self.part_counters.get(part_id, 0)
            last_min = self.part_last_minute.get(part_id, 0)

            # Цвет для части тела
            color = self.part_colors.get(part_id, (255, 255, 255))
            cv2.circle(frame, (panel_x + 8, y_offset - 4), 5, color, -1)

            # Название
            cv2.putText(
                frame,
                part_name,
                (panel_x + 20, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (255, 255, 255),
                1,
            )

            # Общее количество
            text_color = (
                (0, 255, 0)
                if total < 30
                else (0, 165, 255)
                if total < 60
                else (0, 0, 255)
            )
            cv2.putText(
                frame,
                str(total),
                (panel_x + 170, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                text_color,
                1,
            )

            # За последнюю минуту
            text_color = (
                (0, 255, 0)
                if last_min < 10
                else (0, 165, 255)
                if last_min < 20
                else (0, 0, 255)
            )
            cv2.putText(
                frame,
                str(last_min),
                (panel_x + 245, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                text_color,
                1,
            )

            # Прогресс-бар (общий)
            bar_width = int((total / max(1, max(self.part_counters.values()))) * 60)
            cv2.rectangle(
                frame,
                (panel_x + 260, y_offset - 8),
                (panel_x + 260 + bar_width, y_offset - 2),
                color,
                -1,
            )

            y_offset += 22
            if y_offset > panel_y + panel_h - 20:
                break

        return frame

    def reset_statistics(self):
        """Полностью очищает всю статистику перед новым видео"""

        # Очищаем счётчики для критических частей
        for part_id in self.critical_parts.keys():
            self.part_counters[part_id] = 0
            self.part_last_minute[part_id] = 0
            self.part_history[part_id].clear()

        # Очищаем общую статистику
        self.total_movements = 0
        self.last_minute_total = 0

        # Очищаем временные данные
        self.movement_times.clear()
        self.recent_movements.clear()

        # Если есть ещё какие-то хранилища - очищаем их
        if hasattr(self, "peaks_history"):
            self.peaks_history.clear()

        if hasattr(self, "time_bins"):
            for key in self.time_bins:
                self.time_bins[key] = 0

        if hasattr(self, "bin_accels"):
            for key in self.bin_accels:
                self.bin_accels[key].clear()

        print("✓ Statistics reset for new video")  # Отладка

    def _draw_movement_log(self, frame):
        # """Рисует лог последних движений"""
        # if not self.recent_movements:
        #     return frame

        # h, w = frame.shape[:2]

        # # Панель лога (правый верхний угол)
        # log_w, log_h = 280, 250
        # log_x = w - log_w - 10
        # log_y = 50

        # # Фон
        # overlay = frame.copy()
        # cv2.rectangle(
        #     overlay, (log_x, log_y), (log_x + log_w, log_y + log_h), (0, 0, 0), -1
        # )
        # frame = cv2.addWeighted(overlay, 0.85, frame, 0.15, 0)
        # cv2.rectangle(
        #     frame, (log_x, log_y), (log_x + log_w, log_y + log_h), (0, 200, 0), 2
        # )

        # # Заголовок
        # cv2.putText(
        #     frame,
        #     "RECENT MOVEMENTS",
        #     (log_x + 10, log_y + 25),
        #     cv2.FONT_HERSHEY_SIMPLEX,
        #     0.5,
        #     (0, 255, 0),
        #     1,
        # )
        # cv2.line(
        #     frame, (log_x, log_y + 35), (log_x + log_w, log_y + 35), (100, 100, 100), 1
        # )

        # # Список движений
        # y_offset = log_y + 55
        # for i, move in enumerate(reversed(list(self.recent_movements))):
        #     if i >= 8:
        #         break

        #     # Цвет в зависимости от интенсивности
        #     if move["intensity"] > 7:
        #         color = (0, 0, 255)
        #     elif move["intensity"] > 4:
        #         color = (0, 165, 255)
        #     else:
        #         color = (0, 255, 0)

        #     # Название части
        #     cv2.putText(
        #         frame,
        #         move["part"],
        #         (log_x + 10, y_offset),
        #         cv2.FONT_HERSHEY_SIMPLEX,
        #         0.4,
        #         (255, 255, 255),
        #         1,
        #     )

        #     # Интенсивность
        #     cv2.putText(
        #         frame,
        #         f"Intensity: {move['intensity']}/10",
        #         (log_x + 130, y_offset),
        #         cv2.FONT_HERSHEY_SIMPLEX,
        #         0.35,
        #         color,
        #         1,
        #     )

        #     # Прогресс-бар интенсивности
        #     bar_w = int((move["intensity"] / 10) * 80)
        #     cv2.rectangle(
        #         frame,
        #         (log_x + 10, y_offset + 12),
        #         (log_x + 10 + bar_w, y_offset + 18),
        #         color,
        #         -1,
        #     )

        #     y_offset += 25

        return frame

    def get_part_statistics(self):
        """Возвращает статистику по частям тела"""
        return {
            "total_counts": dict(self.part_counters),
            "last_minute_counts": dict(self.part_last_minute),
            "total_movements": self.total_movements,
            "last_minute_total": self.last_minute_total,
            "critical_parts": self.critical_parts,
        }
