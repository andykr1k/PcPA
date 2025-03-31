from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, QSize
import random
import math

class RobotFaceWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_talking = False
        self.mouth_state = 0  # 0: closed, 1-3: open states
        self.mouth_timer_count = 0

        self.eyes_open = True
        self.blink_duration = 3
        self.blink_counter = 0
        self.time_to_next_blink = random.randint(50, 150)

        self.pupil_offset = QPointF(0, 0)
        self.pupil_target_offset = QPointF(0, 0)
        self.pupil_move_timer_count = 0
        self.time_to_next_pupil_move = random.randint(30, 80)

        # Animation timer
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_timer.start(1000 // 30)  # 30 FPS

        self.setMinimumSize(200, 100)

    def sizeHint(self):
        return QSize(300, 150)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Clear background
        painter.fillRect(self.rect(), Qt.transparent)

        # Set drawing color to white
        pen_width = max(2, int(min(w, h) * 0.015))
        painter.setPen(QPen(Qt.white, pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))

        # Draw Eyes
        eye_width = w * 0.25
        eye_height = h * 0.35
        eye_y = h * 0.25
        eye_spacing = w * 0.08

        left_eye_x = w * 0.5 - eye_spacing / 2 - eye_width
        right_eye_x = w * 0.5 + eye_spacing / 2

        left_eye_rect = QRectF(left_eye_x, eye_y, eye_width, eye_height)
        right_eye_rect = QRectF(right_eye_x, eye_y, eye_width, eye_height)

        if self.eyes_open:
            painter.drawEllipse(left_eye_rect)
            painter.drawEllipse(right_eye_rect)

            pupil_radius = eye_height * 0.25
            pupil_offset_limit_x = eye_width / 2 - pupil_radius
            pupil_offset_limit_y = eye_height / 2 - pupil_radius

            clamped_offset_x = max(-pupil_offset_limit_x, min(pupil_offset_limit_x, self.pupil_offset.x()))
            clamped_offset_y = max(-pupil_offset_limit_y, min(pupil_offset_limit_y, self.pupil_offset.y()))
            current_pupil_offset = QPointF(clamped_offset_x, clamped_offset_y)

            left_pupil_center = left_eye_rect.center() + current_pupil_offset
            right_pupil_center = right_eye_rect.center() + current_pupil_offset

            painter.drawEllipse(left_pupil_center, pupil_radius, pupil_radius)
            painter.drawEllipse(right_pupil_center, pupil_radius, pupil_radius)
        else:
            line_y = eye_y + eye_height / 2
            painter.drawLine(int(left_eye_x), int(line_y), int(left_eye_x + eye_width), int(line_y))
            painter.drawLine(int(right_eye_x), int(line_y), int(right_eye_x + eye_width), int(line_y))

        # Draw Mouth
        mouth_y = h * 0.75
        mouth_width_max = w * 0.4
        mouth_height_max = h * 0.15
        mouth_center_x = w / 2

        if self.is_talking:
            if self.mouth_state == 0:
                mouth_h = mouth_height_max * 0.2
                mouth_w = mouth_width_max * 0.8
            elif self.mouth_state == 1:
                mouth_h = mouth_height_max * 0.6
                mouth_w = mouth_width_max * 0.9
            elif self.mouth_state == 2:
                mouth_h = mouth_height_max * 1.0
                mouth_w = mouth_width_max * 1.0
            else:  # state 3
                mouth_h = mouth_height_max * 0.7
                mouth_w = mouth_width_max * 0.6

            mouth_rect = QRectF(mouth_center_x - mouth_w / 2, mouth_y - mouth_h / 2, mouth_w, mouth_h)
            painter.drawEllipse(mouth_rect)
        else:
            mouth_w = mouth_width_max * 0.7
            painter.drawLine(int(mouth_center_x - mouth_w / 2), int(mouth_y), int(mouth_center_x + mouth_w / 2), int(mouth_y))

    def _update_animation(self):
        changed = False

        # Mouth Animation
        if self.is_talking:
            self.mouth_timer_count += 1
            if self.mouth_timer_count > 2:
                self.mouth_timer_count = 0
                self.mouth_state = random.randint(0, 3)
                changed = True
        elif self.mouth_state != 0:
            self.mouth_state = 0
            changed = True

        # Blinking
        if self.eyes_open:
            self.blink_counter += 1
            if self.blink_counter >= self.time_to_next_blink:
                self.eyes_open = False
                self.blink_counter = 0
                self.time_to_next_blink = random.randint(70, 200)
                changed = True
        else:
            self.blink_counter += 1
            if self.blink_counter >= self.blink_duration:
                self.eyes_open = True
                self.blink_counter = 0
                changed = True

        # Pupil Movement
        self.pupil_move_timer_count += 1
        if self.pupil_move_timer_count >= self.time_to_next_pupil_move:
            self.pupil_move_timer_count = 0
            self.time_to_next_pupil_move = random.randint(40, 100)
            max_offset_x = self.width() * 0.05
            max_offset_y = self.height() * 0.05
            self.pupil_target_offset = QPointF(
                random.uniform(-max_offset_x, max_offset_x),
                random.uniform(-max_offset_y, max_offset_y)
            )

        move_speed = 0.2
        delta = self.pupil_target_offset - self.pupil_offset
        if delta.manhattanLength() > 1.0:
            self.pupil_offset += delta * move_speed
            changed = True
        elif self.pupil_offset != self.pupil_target_offset:
            self.pupil_offset = self.pupil_target_offset
            changed = True

        if changed:
            self.update()

    def start_talking(self):
        if not self.is_talking:
            self.is_talking = True
            self.mouth_state = random.randint(0, 3)
            self.mouth_timer_count = 0
            self.update()

    def stop_talking(self):
        if self.is_talking:
            self.is_talking = False
            self.update()

    def look_at_point(self, target_point: QPointF):
        center = QPointF(self.width() / 2, self.height() / 2)
        vector_to_target = target_point - center

        max_offset_x = self.width() * 0.05
        max_offset_y = self.height() * 0.05

        scale_factor = 0.1
        target_x = max(-max_offset_x, min(max_offset_x, vector_to_target.x() * scale_factor))
        target_y = max(-max_offset_y, min(max_offset_y, vector_to_target.y() * scale_factor))

        self.pupil_target_offset = QPointF(target_x, target_y)

    def start_talking(self):
        print("DEBUG: start_talking called") # Add print for debugging
        if not self.is_talking:
            self.is_talking = True
            self.mouth_state = random.randint(1, 3) # Start with open mouth
            self.mouth_timer_count = 0
            self._update_animation() # Trigger immediate update potentially needed
            # self.update() # Request repaint

    def stop_talking(self):
        print("DEBUG: stop_talking called") # Add print for debugging
        if self.is_talking:
            self.is_talking = False
            # self.mouth_state = 0 # Set explicitly to closed
            # self._update_animation() # Trigger immediate update potentially needed
            # self.update() # Request repaint
