"""
Dedicated window for displaying instructions and action buttons.
Appears in bottom right corner and stays on top.
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QPainter, QColor, QFont, QPainterPath, QMovie
from pathlib import Path


class InstructionWindow(QMainWindow):
    """Window that displays instructions and action buttons in bottom right."""
    
    def __init__(self, instructions: str, gif_path: str = None):
        super().__init__()
        
        self.instructions = instructions
        self.button_result = None  # 'done' or 'cancel' when clicked
        self.gif_path = gif_path
        
        # Set window flags for overlay behavior
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.SplashScreen
        )
        
        # Make window transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set window title
        self.setWindowTitle("Drippy Instructions")
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Add avatar if provided
        self.avatar_label = None
        if gif_path and Path(gif_path).exists():
            self.avatar_label = QLabel()
            self.avatar_label.setScaledContents(True)
            self.avatar_label.setFixedSize(80, 80)
            self.avatar_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.avatar_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            
            movie = QMovie(str(gif_path))
            self.avatar_label.setMovie(movie)
            movie.start()
            
            layout.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Add instructions text
        self.instructions_label = QLabel(instructions)
        self.instructions_label.setWordWrap(True)
        self.instructions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.instructions_label.setFont(font)
        self.instructions_label.setStyleSheet("color: white;")
        layout.addWidget(self.instructions_label)
        
        # Add buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
        # Continue button
        self.continue_button = QPushButton("Continue")
        self.continue_button.setFixedHeight(45)
        self.continue_button.setStyleSheet("""
            QPushButton {
                background-color: #388e3c;
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4caf50;
            }
            QPushButton:pressed {
                background-color: #2e7d32;
            }
        """)
        self.continue_button.clicked.connect(self._on_continue)
        button_layout.addWidget(self.continue_button)
        
        # Exit button
        self.exit_button = QPushButton("Exit")
        self.exit_button.setFixedHeight(45)
        self.exit_button.setStyleSheet("""
            QPushButton {
                background-color: #424242;
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #616161;
            }
            QPushButton:pressed {
                background-color: #212121;
            }
        """)
        self.exit_button.clicked.connect(self._on_exit)
        button_layout.addWidget(self.exit_button)
        
        layout.addLayout(button_layout)
        
        # Calculate size based on content
        self.adjustSize()
        
        # Position in bottom right
        self._position_window()
    
    def _position_window(self):
        """Position window in bottom right corner."""
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen().geometry()
            window_size = self.size()
            x = screen.width() - window_size.width() - 20
            y = screen.height() - window_size.height() - 20
            self.setGeometry(x, y, window_size.width(), window_size.height())
    
    def _on_continue(self):
        """Handle Continue button click."""
        self.button_result = 'done'
        self.close()
    
    def _on_exit(self):
        """Handle Exit button click."""
        self.button_result = 'cancel'
        self.close()
    
    def paintEvent(self, event):
        """Paint the window with rounded corners and background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create rounded rectangle path
        rect = self.rect()
        corner_radius = 12
        path = QPainterPath()
        path.addRoundedRect(
            rect.x(), rect.y(),
            rect.width(), rect.height(),
            corner_radius, corner_radius
        )
        
        # Draw background
        bg_color = QColor(20, 20, 20, 240)
        painter.fillPath(path, bg_color)
        
        # Draw border
        border_color = QColor(255, 255, 255, 100)
        painter.setPen(border_color)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)


def show_instruction_window(instructions: str, gif_path: str = None):
    """
    Show instruction window and return button result.
    
    Args:
        instructions: Text instructions to display
        gif_path: Path to GIF avatar (optional)
        
    Returns:
        'done' if Continue button was clicked, 'cancel' if Exit button was clicked, None if closed otherwise
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create instruction window
    window = InstructionWindow(instructions, gif_path)
    window.show()
    window.raise_()
    
    # Force window to front on macOS
    if sys.platform == 'darwin':
        window.setWindowFlags(
            window.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
        )
        window.show()
        window.raise_()
    
    # Use a local event loop to wait for window to close
    from PyQt5.QtCore import QEventLoop, QTimer
    loop = QEventLoop()
    
    # Keep window on top
    def keep_on_top():
        if window.isVisible():
            window.raise_()
            window.setWindowFlags(
                window.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
            )
            window.show()
    
    keep_top_timer = QTimer()
    keep_top_timer.timeout.connect(keep_on_top)
    keep_top_timer.start(100)
    
    def check_closed():
        if not window.isVisible():
            keep_top_timer.stop()
            loop.quit()
    
    close_timer = QTimer()
    close_timer.timeout.connect(check_closed)
    close_timer.start(50)
    
    def on_destroyed():
        keep_top_timer.stop()
        close_timer.stop()
        loop.quit()
    
    window.destroyed.connect(on_destroyed)
    
    loop.exec()
    
    keep_top_timer.stop()
    close_timer.stop()
    
    return window.button_result

