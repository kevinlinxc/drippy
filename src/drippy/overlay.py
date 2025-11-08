import sys
import argparse
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QColor, QKeyEvent


class OverlayWindow(QMainWindow):
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
            Qt.WindowType.X11BypassWindowManagerHint |
            Qt.WindowType.Tool
        )
        
        # Make window transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set window title (for debugging)
        self.setWindowTitle("Bounding Box Overlay")
        
        # Enable keyboard focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def paintEvent(self, event):
        """Paint the overlay with dark background and transparent hole for bounding box."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get window geometry
        window_rect = self.rect()
        bbox_rect = QRect(self.bbox_x, self.bbox_y, self.bbox_width, self.bbox_height)
        
        # Draw dark semi-transparent overlay in four regions around the bounding box
        dark_color = QColor(0, 0, 0, 200)  # Black with 200/255 opacity
        
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
        
        # Draw a border around the highlighted area
        border_color = QColor(255, 255, 255, 255)  # White border
        painter.setPen(border_color)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(bbox_rect)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events - close on Escape."""
        if event.key() == Qt.Key.Key_Escape:
            QApplication.instance().quit()
        super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        """Allow clicking through the overlay (except on the highlighted area)."""
        # Check if click is within bounding box
        bbox_rect = QRect(self.bbox_x, self.bbox_y, self.bbox_width, self.bbox_height)
        if not bbox_rect.contains(event.pos()):
            # Click outside bounding box - close overlay
            QApplication.instance().quit()
        super().mousePressEvent(event)


def main():
    parser = argparse.ArgumentParser(
        description='Create a screen overlay highlighting a bounding box area'
    )
    parser.add_argument('x', type=int, help='X coordinate of bounding box')
    parser.add_argument('y', type=int, help='Y coordinate of bounding box')
    parser.add_argument('width', type=int, help='Width of bounding box')
    parser.add_argument('height', type=int, help='Height of bounding box')
    
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    
    # Create overlay window
    window = OverlayWindow(args.x, args.y, args.width, args.height)
    
    # Get screen geometry and set window to cover entire screen
    screen = app.primaryScreen().geometry()
    window.setGeometry(screen)
    
    window.show()
    window.raise_()
    window.activateWindow()
    window.setFocus()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

