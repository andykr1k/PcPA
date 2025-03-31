from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication
from PyQt5.QtGui import QPainter, QColor, QPen, QLinearGradient
from PyQt5.QtCore import Qt, QTimer, QPointF, QSize
from .robot_face import RobotFaceWidget
from Utils import config
import math

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Make window frameless and transparent
        self.setWindowFlags(
            Qt.FramelessWindowHint |        # No border, title bar, etc.
            Qt.WindowStaysOnTopHint |      # Keep it above other windows
            Qt.Tool                        # Try to prevent showing in taskbar
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Get screen geometry
        self.screen_geometry = QApplication.primaryScreen().geometry()

        # Create the face widget - Give it a reference to self if needed, or use signals
        self.face_widget = RobotFaceWidget(self)

        # Set up layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.face_widget)
        layout.setContentsMargins(0, 0, 0, 0) # No internal margins for the layout
        self.setLayout(layout)

        # Rainbow gradient animation
        self.gradient_angle = 0
        self.gradient_timer = QTimer(self)
        self.gradient_timer.timeout.connect(self._update_gradient)
        # Use interval from config
        self.gradient_timer.start(config.GRADIENT_UPDATE_INTERVAL)

        # Initially hide the window
        self.hide()

        # Enable mouse tracking for eye movement
        self.setMouseTracking(True)

        # Maximize initially to set up correct size ratios
        self._setup_initial_geometry()


    def _setup_initial_geometry(self):
        """Sets initial fullscreen geometry and face size."""
        self.setGeometry(self.screen_geometry)
        # Calculate initial face size based on screen and config scale
        face_w = int(self.screen_geometry.width() * config.MAXIMIZED_FACE_SCALE_W)
        face_h = int(self.screen_geometry.height() * config.MAXIMIZED_FACE_SCALE_H)
        self.face_widget.setFixedSize(face_w, face_h)
        # Center the face widget manually within the layout (since layout might add margins)
        # This might need adjustment depending on exact layout behavior
        margins = self.layout().contentsMargins()
        available_w = self.width() - margins.left() - margins.right()
        available_h = self.height() - margins.top() - margins.bottom()
        face_x = margins.left() + (available_w - face_w) // 2
        face_y = margins.top() + (available_h - face_h) // 2
        # self.face_widget.move(face_x, face_y) # Usually layout handles this, check if needed

    def _update_gradient(self):
        """Updates the rainbow gradient animation."""
        self.gradient_angle = (self.gradient_angle + 1) % 360
        self.update() # Request a repaint

    def paintEvent(self, event):
        """Draws the rainbow gradient border."""
        if not self.isVisible() or self.isMinimized(): # Don't draw if hidden or minimized without border
             # Clear background even when hidden/minimized to ensure transparency
            painter = QPainter(self)
            painter.fillRect(self.rect(), Qt.transparent)
            return # Skip drawing border if minimized or hidden

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Create rainbow gradient
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        # Radius slightly larger to ensure gradient covers corners well
        radius = math.sqrt(center_x**2 + center_y**2)

        # Convert angle to radians
        angle_rad = math.radians(self.gradient_angle) # Use math.radians

        # Calculate start and end points for the gradient rotation
        start_x = center_x + radius * math.cos(angle_rad)
        start_y = center_y + radius * math.sin(angle_rad)
        end_x = center_x - radius * math.cos(angle_rad) # Opposite direction
        end_y = center_y - radius * math.sin(angle_rad) # Opposite direction

        gradient = QLinearGradient(QPointF(start_x, start_y), QPointF(end_x, end_y))
        # Smooth Rainbow Colors
        gradient.setColorAt(0.0, QColor(255, 0, 0))     # Red
        gradient.setColorAt(1.0/6.0, QColor(255, 165, 0)) # Orange
        gradient.setColorAt(2.0/6.0, QColor(255, 255, 0)) # Yellow
        gradient.setColorAt(3.0/6.0, QColor(0, 255, 0))   # Green
        gradient.setColorAt(4.0/6.0, QColor(0, 0, 255))   # Blue
        gradient.setColorAt(5.0/6.0, QColor(75, 0, 130))  # Indigo
        gradient.setColorAt(1.0, QColor(238, 130, 238)) # Violet (or repeat Red for seamless loop)
        # gradient.setColorAt(1.0, QColor(255, 0, 0)) # Option: Repeat Red for seamless loop

        # Draw border using config width
        border_width = config.BORDER_WIDTH
        pen = QPen(gradient, border_width)
        pen.setCapStyle(Qt.FlatCap) # Use flat cap for cleaner corners
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        # Draw rectangle slightly inset so the pen width is centered on the edge
        draw_rect = self.rect().adjusted(border_width // 2, border_width // 2, -border_width // 2, -border_width // 2)
        painter.drawRect(draw_rect)

    def mouseMoveEvent(self, event):
        """Forward mouse position to face widget for eye tracking."""
        # Convert global mouse coordinates to coordinates relative to the face widget
        if self.face_widget.isVisible():
            relative_pos = self.face_widget.mapFromGlobal(event.globalPos())
            self.face_widget.look_at_point(relative_pos)

    def minimize(self):
        """Minimize the window to the top-left corner."""
        # Use dimensions from config
        self.setGeometry(
            config.MINIMIZED_X,
            config.MINIMIZED_Y,
            config.MINIMIZED_WIDTH,
            config.MINIMIZED_HEIGHT
        )
        # Resize face using config dimensions
        self.face_widget.setFixedSize(
            config.MINIMIZED_FACE_WIDTH,
            config.MINIMIZED_FACE_HEIGHT
        )
        # Ensure the face is centered or positioned correctly if layout doesn't do it
        # self.face_widget.move(config.BORDER_WIDTH // 2, config.BORDER_WIDTH // 2) # Example if needed
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint) # Optional: Allow minimized window to go behind others
        self.show() # Ensure it's visible if it was hidden
        self.update() # Repaint to remove border if paintEvent checks isMinimized()

    def maximize(self):
        """Maximize the window to fullscreen."""
        # Restore Always On Top flag if it was removed
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setGeometry(self.screen_geometry)
        # Recalculate face size based on config scale
        face_w = int(self.screen_geometry.width() * config.MAXIMIZED_FACE_SCALE_W)
        face_h = int(self.screen_geometry.height() * config.MAXIMIZED_FACE_SCALE_H)
        self.face_widget.setFixedSize(face_w, face_h)
        # Center face widget again if necessary
        # face_x = (self.width() - face_w) // 2
        # face_y = (self.height() - face_h) // 2
        # self.face_widget.move(face_x, face_y)
        self.show()
        self.raise_() # Bring window to front
        self.activateWindow() # Try to give it focus if possible

    def setup_voice_controller(self, voice_controller):
        """Connect voice controller signals after initialization."""
        self.voice_controller = voice_controller
        self.voice_controller.show_window.connect(self.maximize, Qt.QueuedConnection)
        self.voice_controller.minimize_window.connect(self.minimize, Qt.QueuedConnection)
        self.voice_controller.close_window.connect(self.hide, Qt.QueuedConnection)

        self.voice_controller.started_speaking.connect(self.face_widget.start_talking, Qt.QueuedConnection)
        self.voice_controller.finished_speaking.connect(self.face_widget.stop_talking, Qt.QueuedConnection)