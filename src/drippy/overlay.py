"""
Simple overlay that highlights a bounding box and closes on click.
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QColor, QMouseEvent


class OverlayWindow(QMainWindow):
    """Simple overlay window that highlights a bounding box."""
    
    def __init__(self, x, y, width, height):
        super().__init__()
        
        # Store the bounding box coordinates
        self.bbox_x = x
        self.bbox_y = y
        self.bbox_width = width
        self.bbox_height = height
        
        # Set window flags for overlay behavior
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.SplashScreen |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        
        # Make window transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Don't steal focus
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        
        # Set window title
        self.setWindowTitle("Bounding Box Overlay")
    
    def paintEvent(self, event):
        """Paint the overlay with dark background and transparent hole for bounding box."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get window geometry
        window_rect = self.rect()
        bbox_rect = QRect(self.bbox_x, self.bbox_y, self.bbox_width, self.bbox_height)
        
        # Draw dark semi-transparent overlay in four regions around the bounding box
        dark_color = QColor(0, 0, 0, 100)  # Black with 100/255 opacity
        
        # Top rectangle
        if bbox_rect.top() > window_rect.top():
            painter.fillRect(
                window_rect.left(), window_rect.top(),
                window_rect.width(), bbox_rect.top() - window_rect.top(),
                dark_color
            )
        
        # Bottom rectangle
        if bbox_rect.bottom() < window_rect.bottom():
            painter.fillRect(
                window_rect.left(), bbox_rect.bottom(),
                window_rect.width(), window_rect.bottom() - bbox_rect.bottom(),
                dark_color
            )
        
        # Left rectangle
        if bbox_rect.left() > window_rect.left():
            painter.fillRect(
                window_rect.left(), bbox_rect.top(),
                bbox_rect.left() - window_rect.left(), bbox_rect.height(),
                dark_color
            )
        
        # Right rectangle
        if bbox_rect.right() < window_rect.right():
            painter.fillRect(
                bbox_rect.right(), bbox_rect.top(),
                window_rect.right() - bbox_rect.right(), bbox_rect.height(),
                dark_color
            )
        
        # Draw a glowing border around the highlighted area
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Outer glow layers (drawn from outside to inside)
        glow_layers = [
            (8, 30),   # width 8, opacity 30
            (6, 60),   # width 6, opacity 60
            (4, 90),   # width 4, opacity 90
            (2, 120),  # width 2, opacity 120
        ]
        
        for width, opacity in glow_layers:
            glow_color = QColor(255, 255, 255, opacity)
            pen = painter.pen()
            pen.setColor(glow_color)
            pen.setWidth(width)
            painter.setPen(pen)
            # Draw slightly larger rect for each glow layer
            offset = width // 2
            glow_rect = QRect(
                bbox_rect.x() - offset,
                bbox_rect.y() - offset,
                bbox_rect.width() + width,
                bbox_rect.height() + width
            )
            painter.drawRect(glow_rect)
        
        # Main border (solid white)
        border_color = QColor(255, 255, 255, 255)
        pen = painter.pen()
        pen.setColor(border_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(bbox_rect)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Close overlay immediately on click."""
        self.close()
        super().mousePressEvent(event)


def show_overlay(x, y, width, height):
    """
    Show overlay highlighting the bounding box area.
    Overlay closes on first click.
    
    Args:
        x: X coordinate of bounding box
        y: Y coordinate of bounding box
        width: Width of bounding box
        height: Height of bounding box
    """
    # Check if QApplication already exists
    app = QApplication.instance()
    if app is None:
        # Create new QApplication if it doesn't exist
        app = QApplication(sys.argv)
    
    # Create overlay window
    window = OverlayWindow(x, y, width, height)
    
    # Get screen geometry and set window to cover entire screen
    screen = app.primaryScreen().geometry()
    window.setGeometry(screen)
    
    window.show()
    window.raise_()
    
    # Force window to front on macOS to appear above dock
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
    
    # Run event loop until window closes
    loop.exec()
    
    keep_top_timer.stop()
    close_timer.stop()
