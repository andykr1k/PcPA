import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, QSize

class RobotFaceWidget(QWidget):
    """Widget responsible for drawing the robot face."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_talking = False
        self.mouth_state = 0  # 0: closed, 1-3: open states
        self.mouth_timer_count = 0

        self.eyes_open = True
        self.blink_duration = 3 # How many timer ticks the blink lasts
        self.blink_counter = 0
        self.time_to_next_blink = random.randint(50, 150) # Ticks until next blink

        # Simple eye pupil movement simulation (offset from center)
        # For more advanced, you could track the mouse or use random walks
        self.pupil_offset = QPointF(0, 0)
        self.pupil_target_offset = QPointF(0, 0)
        self.pupil_move_timer_count = 0
        self.time_to_next_pupil_move = random.randint(30, 80)


        # Animation timer
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._update_animation)
        # Update rate (e.g., 15 times per second for smoother animation)
        self.animation_timer.start(1000 // 15) # ms per frame

        # Set minimum size hint for the widget
        self.setMinimumSize(200, 100)


    def sizeHint(self):
        # Provide a default size for the widget
        return QSize(300, 150)

    def paintEvent(self, event):
        """Handles the drawing of the face."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Get widget dimensions
        w = self.width()
        h = self.height()

        # Clear background (needed for transparency updates)
        painter.fillRect(self.rect(), Qt.transparent)

        # Set drawing color to white
        pen_width = max(2, int(min(w, h) * 0.015)) # Scale pen width slightly
        painter.setPen(QPen(Qt.white, pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))

        # --- Draw Eyes ---
        eye_width = w * 0.25
        eye_height = h * 0.35
        eye_y = h * 0.25
        eye_spacing = w * 0.08 # Space between eyes

        left_eye_x = w * 0.5 - eye_spacing / 2 - eye_width
        right_eye_x = w * 0.5 + eye_spacing / 2

        # Define eye rects
        left_eye_rect = QRectF(left_eye_x, eye_y, eye_width, eye_height)
        right_eye_rect = QRectF(right_eye_x, eye_y, eye_width, eye_height)

        if self.eyes_open:
            # Draw eye outlines (optional, looks better with fill only sometimes)
            # painter.setBrush(Qt.NoBrush) # Uncomment if you only want outlines
            # painter.drawEllipse(left_eye_rect)
            # painter.drawEllipse(right_eye_rect)
            # painter.setBrush(QBrush(Qt.white, Qt.SolidPattern)) # Reset brush

            # Draw filled eyes
            painter.drawEllipse(left_eye_rect)
            painter.drawEllipse(right_eye_rect)

            # Draw pupils (small filled circles) - slightly offsettable
            pupil_radius = eye_height * 0.25
            pupil_offset_limit_x = eye_width / 2 - pupil_radius
            pupil_offset_limit_y = eye_height / 2 - pupil_radius

            # Clamp pupil offset within eye bounds
            clamped_offset_x = max(-pupil_offset_limit_x, min(pupil_offset_limit_x, self.pupil_offset.x()))
            clamped_offset_y = max(-pupil_offset_limit_y, min(pupil_offset_limit_y, self.pupil_offset.y()))
            current_pupil_offset = QPointF(clamped_offset_x, clamped_offset_y)

            left_pupil_center = left_eye_rect.center() + current_pupil_offset
            right_pupil_center = right_eye_rect.center() + current_pupil_offset

            # Use a darker color or black for pupils if preferred
            # painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))
            # painter.setPen(Qt.NoPen) # No outline for pupils

            painter.drawEllipse(left_pupil_center, pupil_radius, pupil_radius)
            painter.drawEllipse(right_pupil_center, pupil_radius, pupil_radius)

            # Reset brush and pen if changed for pupils
            # painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))
            # painter.setPen(QPen(Qt.white, pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

        else:
            # Draw closed eyes (lines)
            line_y = eye_y + eye_height / 2
            painter.drawLine(int(left_eye_x), int(line_y), int(left_eye_x + eye_width), int(line_y))
            painter.drawLine(int(right_eye_x), int(line_y), int(right_eye_x + eye_width), int(line_y))


        # --- Draw Mouth ---
        mouth_y = h * 0.75
        mouth_width_max = w * 0.4
        mouth_height_max = h * 0.15
        mouth_center_x = w / 2

        if self.is_talking:
            # Animate mouth shape based on mouth_state
            if self.mouth_state == 0: # Slightly open
                 mouth_h = mouth_height_max * 0.2
                 mouth_w = mouth_width_max * 0.8
                 mouth_rect = QRectF(mouth_center_x - mouth_w / 2, mouth_y - mouth_h / 2, mouth_w, mouth_h)
                 painter.drawEllipse(mouth_rect)
            elif self.mouth_state == 1: # Medium open
                 mouth_h = mouth_height_max * 0.6
                 mouth_w = mouth_width_max * 0.9
                 mouth_rect = QRectF(mouth_center_x - mouth_w / 2, mouth_y - mouth_h / 2, mouth_w, mouth_h)
                 painter.drawEllipse(mouth_rect)
            elif self.mouth_state == 2: # Fully open
                 mouth_h = mouth_height_max * 1.0
                 mouth_w = mouth_width_max * 1.0
                 mouth_rect = QRectF(mouth_center_x - mouth_w / 2, mouth_y - mouth_h / 2, mouth_w, mouth_h)
                 painter.drawEllipse(mouth_rect)
            elif self.mouth_state == 3: # O shape / smaller
                 mouth_h = mouth_height_max * 0.7
                 mouth_w = mouth_width_max * 0.6
                 mouth_rect = QRectF(mouth_center_x - mouth_w / 2, mouth_y - mouth_h / 2, mouth_w, mouth_h)
                 painter.drawEllipse(mouth_rect)

        else:
            # Draw closed mouth (line)
            mouth_w = mouth_width_max * 0.7
            painter.drawLine(int(mouth_center_x - mouth_w / 2), int(mouth_y), int(mouth_center_x + mouth_w / 2), int(mouth_y))


    def _update_animation(self):
        """Updates animation states periodically."""
        changed = False # Flag to check if repaint is needed

        # --- Mouth Animation ---
        if self.is_talking:
            self.mouth_timer_count += 1
            # Change mouth shape every few frames (adjust timing as needed)
            if self.mouth_timer_count > 2:
                self.mouth_timer_count = 0
                self.mouth_state = random.randint(0, 3) # Cycle through states randomly
                changed = True
        elif self.mouth_state != 0:
             # If stopped talking, ensure mouth is reset visually
             self.mouth_state = 0 # Or whatever your 'closed' state index is
             changed = True


        # --- Blinking ---
        if self.eyes_open:
            self.blink_counter += 1
            if self.blink_counter >= self.time_to_next_blink:
                self.eyes_open = False
                self.blink_counter = 0 # Reset counter for blink duration
                self.time_to_next_blink = random.randint(70, 200) # Time for next blink
                changed = True
        else: # Eyes are closed
            self.blink_counter += 1
            if self.blink_counter >= self.blink_duration:
                self.eyes_open = True
                self.blink_counter = 0 # Reset counter for time TO next blink
                changed = True


        # --- Pupil Movement ---
        self.pupil_move_timer_count += 1
        if self.pupil_move_timer_count >= self.time_to_next_pupil_move:
             self.pupil_move_timer_count = 0
             self.time_to_next_pupil_move = random.randint(40, 100)
             # Set a new random target offset
             max_offset_x = self.width() * 0.05
             max_offset_y = self.height() * 0.05
             self.pupil_target_offset = QPointF(
                 random.uniform(-max_offset_x, max_offset_x),
                 random.uniform(-max_offset_y, max_offset_y)
             )
             # We won't implement smooth interpolation here for simplicity,
             # but will just move towards the target slightly each frame below

        # Simple interpolation towards target pupil offset
        move_speed = 0.2 # Adjust for faster/slower eye movement
        delta = self.pupil_target_offset - self.pupil_offset
        if delta.manhattanLength() > 1.0: # Move if not already very close
            self.pupil_offset += delta * move_speed
            changed = True
        elif self.pupil_offset != self.pupil_target_offset: # Snap to target if close
             self.pupil_offset = self.pupil_target_offset
             changed = True


        # Trigger repaint only if something visually changed
        if changed:
            self.update()

    # --- Public Methods to Control Face ---
    def start_talking(self):
        """Call this when the AI starts speaking."""
        if not self.is_talking:
            self.is_talking = True
            self.mouth_state = random.randint(0, 3) # Start with a random open state
            self.mouth_timer_count = 0 # Reset timer
            self.update() # Immediate update

    def stop_talking(self):
        """Call this when the AI stops speaking."""
        if self.is_talking:
            self.is_talking = False
            # self.mouth_state = 0 # Set to closed state immediately
            # No need to explicitly set mouth_state=0 here,
            # the animation loop will handle it on the next tick
            # self.update() # Update may not be needed if animation loop handles reset

    def look_at_point(self, target_point: QPointF):
        """ Experimental: Make eyes look towards a point (relative to widget) """
        center = QPointF(self.width() / 2, self.height() / 2)
        vector_to_target = target_point - center

        # Normalize and scale the vector to represent pupil offset
        # Crude scaling - needs refinement based on eye size/shape
        max_offset_x = self.width() * 0.05
        max_offset_y = self.height() * 0.05

        # Scale the vector but limit its magnitude
        scale_factor = 0.1 # How strongly the eyes react
        target_x = max(-max_offset_x, min(max_offset_x, vector_to_target.x() * scale_factor))
        target_y = max(-max_offset_y, min(max_offset_y, vector_to_target.y() * scale_factor))

        self.pupil_target_offset = QPointF(target_x, target_y)
        # The animation loop will handle moving towards this target


class MainWindow(QWidget):
    """Main application window (transparent, frameless)."""
    def __init__(self):
        super().__init__()

        # Make window frameless and transparent
        self.setWindowFlags(
            Qt.FramelessWindowHint |        # No border, title bar, etc.
            Qt.WindowStaysOnTopHint |      # Keep it above other windows
            Qt.Tool                        # Try to prevent showing in taskbar (OS dependent)
            # Qt.WindowTransparentForInput # Use if you need clicks to pass *through* the window
        )
        # This attribute is crucial for transparency
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Set initial size and position (optional)
        self.setGeometry(100, 100, 400, 200) # x, y, width, height

        # Create the face widget
        self.face_widget = RobotFaceWidget(self)

        # Set up layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.face_widget)
        layout.setContentsMargins(0,0,0,0) # No padding around the face widget
        self.setLayout(layout)

        # --- Example Control ---
        # Simulate talking for a few seconds using timers
        self.talk_timer = QTimer(self)
        self.talk_timer.setSingleShot(True)
        self.talk_timer.timeout.connect(self.face_widget.start_talking)
        # self.talk_timer.start(2000) # Start talking after 2 seconds

        self.stop_talk_timer = QTimer(self)
        self.stop_talk_timer.setSingleShot(True)
        self.stop_talk_timer.timeout.connect(self.face_widget.stop_talking)
        # self.stop_talk_timer.start(7000) # Stop talking after 7 seconds

        # --- Mouse Interaction Example ---
        self.setMouseTracking(True) # Enable mouse tracking for the main window

    def mouseMoveEvent(self, event):
        """ Forward mouse position to face widget for eye tracking """
        # Convert global mouse position to position relative to the face widget
        relative_pos = self.face_widget.mapFromGlobal(event.globalPos())
        self.face_widget.look_at_point(relative_pos)
        # print(f"Mouse at: {relative_pos}") # For debugging

    def mousePressEvent(self, event):
        """ Example: Start talking on click """
        if not self.face_widget.is_talking:
            self.face_widget.start_talking()
            # Maybe stop after a few seconds if you click
            self.stop_talk_timer.start(4000)
        else:
            self.face_widget.stop_talking()

    def keyPressEvent(self, event):
        """Close window on ESC key press."""
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Space: # Toggle talking with space bar
             if self.face_widget.is_talking:
                 self.face_widget.stop_talking()
             else:
                 self.face_widget.start_talking()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # It's generally good practice for transparent widgets
    # Force the use of a compositing manager if available.
    # This might not be strictly necessary on all systems but can help.
    try:
        from PyQt5.QtX11Extras import QX11Info # Linux specific - check platform?
        if QX11Info.isCompositingManagerRunning():
             # Set ARGB visual - might improve transparency handling
             # This part is advanced and platform specific, often not needed
             # print("Compositing manager running.")
             pass
    except ImportError:
        # QtX11Extras not available (Windows, macOS, or Linux without it)
        pass


    window = MainWindow()
    window.show()

    sys.exit(app.exec_())