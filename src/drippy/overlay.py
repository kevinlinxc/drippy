import sys
import argparse
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QColor, QKeyEvent, QFont, QPainterPath, QMouseEvent, QMovie


class OverlayWindow(QMainWindow):
    def __init__(self, x, y, width, height, text=""):
        super().__init__()
        
        # Store the bounding box coordinates
        self.bbox_x = x
        self.bbox_y = y
        self.bbox_width = width
        self.bbox_height = height
        self.text = text
        
        # Store button rectangles and hover states
        self.done_button_rect = None
        self.cancel_button_rect = None
        self.done_hovered = False
        self.cancel_hovered = False
        self.button_result = None  # 'done' or 'cancel' when clicked
        
        # GIF character
        self.character_label = None
        self.character_movie = None
        self.character_size = 120  # Size of the character GIF
        
        # Set window flags for overlay behavior
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.SplashScreen |  # SplashScreen has higher z-order than Tool
            Qt.WindowType.WindowDoesNotAcceptFocus  # Don't steal focus from other windows
        )
        
        # Make window transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Make window always stay on top, even when other apps are activated
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        
        # On macOS, set window level to be above dock
        if sys.platform == 'darwin':
            try:
                from PyQt5.QtCore import QTimer
                # Use a timer to set window level after window is created
                QTimer.singleShot(0, self._set_macos_window_level)
            except Exception:
                pass
        
        # Set window title (for debugging)
        self.setWindowTitle("Bounding Box Overlay")
        
        # Enable keyboard focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Load and setup GIF character
        self._setup_character()
    
    def _setup_character(self):
        """Setup the animated GIF character."""
        # Find the GIF file (look in project root)
        project_root = Path(__file__).parent.parent.parent
        gif_path = project_root / "bouncing_droplet_refined_hat.gif"
        
        if not gif_path.exists():
            # Try alternative locations
            gif_path = Path("bouncing_droplet_refined_hat.gif")
            if not gif_path.exists():
                return
        
        # Create QLabel for the character
        self.character_label = QLabel(self)
        self.character_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.character_label.setScaledContents(True)
        # Make label not interfere with mouse events (click-through)
        self.character_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # Load and start the GIF animation
        self.character_movie = QMovie(str(gif_path))
        self.character_label.setMovie(self.character_movie)
        self.character_movie.start()
        
        # Set size
        self.character_label.setFixedSize(self.character_size, self.character_size)
    
    def _set_macos_window_level(self):
        """Set macOS window level to be above dock using Objective-C APIs."""
        # The SplashScreen window flag should already provide high z-order
        # If needed, we can add PyObjC-based window level setting here
        pass
    
    def paintEvent(self, event):
        """Paint the overlay with dark background and transparent hole for bounding box."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get window geometry
        window_rect = self.rect()
        bbox_rect = QRect(self.bbox_x, self.bbox_y, self.bbox_width, self.bbox_height)
        
        # Draw dark semi-transparent overlay in four regions around the bounding box
        dark_color = QColor(0, 0, 0, 100)  # Black with 100/255 opacity (lighter)
        
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
        # Draw multiple borders with decreasing opacity to create glow effect
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
        
        # Draw text instructions with character and speech bubble
        if self.text:
            # Set font for text
            font = QFont()
            font.setPointSize(15)
            font.setBold(True)
            painter.setFont(font)
            
            # Position character to the right of the bounding box
            character_spacing = 20
            character_x = bbox_rect.right() + character_spacing
            character_y = bbox_rect.top()
            
            # Position text box to the right of the character
            text_x = character_x + self.character_size + 15
            text_y = bbox_rect.top()
            
            # Calculate text dimensions
            font_metrics = painter.fontMetrics()
            text_width = font_metrics.horizontalAdvance(self.text)
            text_height = font_metrics.height()
            
            # Draw text with a rounded semi-transparent background for readability
            bg_padding_x = 16
            bg_padding_y = 12
            bg_rect = QRect(
                text_x - bg_padding_x,
                text_y,
                text_width + bg_padding_x * 2,
                text_height + bg_padding_y * 2
            )
            
            # Create speech bubble path with tail pointing to character
            corner_radius = 12
            bubble_path = QPainterPath()
            bubble_path.addRoundedRect(
                bg_rect.x(), bg_rect.y(),
                bg_rect.width(), bg_rect.height(),
                corner_radius, corner_radius
            )
            
            # Add speech bubble tail pointing left toward character
            tail_width = 15
            tail_height = 12
            tail_x = bg_rect.left()  # Tail on the left side of the bubble
            tail_y = bg_rect.top() + 20  # Position tail near top-middle
            
            tail_points = [
                (tail_x, tail_y),
                (tail_x - tail_width, tail_y + tail_height // 2),
                (tail_x, tail_y + tail_height)
            ]
            tail_polygon = QPainterPath()
            tail_polygon.moveTo(tail_points[0][0], tail_points[0][1])
            tail_polygon.lineTo(tail_points[1][0], tail_points[1][1])
            tail_polygon.lineTo(tail_points[2][0], tail_points[2][1])
            tail_polygon.closeSubpath()
            bubble_path = bubble_path.united(tail_polygon)
            
            # Draw semi-transparent background with rounded corners
            bg_color = QColor(20, 20, 20, 220)  # Dark semi-transparent background
            painter.fillPath(bubble_path, bg_color)
            
            # Draw subtle border for better definition
            border_color = QColor(255, 255, 255, 80)  # Subtle white border
            pen = painter.pen()
            pen.setColor(border_color)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawPath(bubble_path)
            
            # Draw text in white with slight shadow for better readability
            text_color = QColor(255, 255, 255, 255)
            painter.setPen(text_color)
            painter.drawText(
                text_x,
                text_y + font_metrics.ascent() + bg_padding_y,
                self.text
            )
            
            # Position and show character GIF
            if self.character_label:
                self.character_label.move(character_x, character_y)
                self.character_label.show()
                self.character_label.raise_()
            
            # Draw buttons below the text box
            button_spacing = 10
            button_y = bg_rect.bottom() + 15
            button_width = 100
            button_height = 40
            button_corner_radius = 8
            
            # Continue button (primary, green/blue)
            # Calculate button width based on text width
            button_font = QFont()
            button_font.setPointSize(13)
            button_font.setBold(True)
            painter.setFont(button_font)
            button_font_metrics = painter.fontMetrics()
            continue_text_width = button_font_metrics.horizontalAdvance("Continue")
            button_width = max(100, continue_text_width + 24)  # Ensure minimum width with padding
            
            continue_button_x = text_x - bg_padding_x
            self.done_button_rect = QRect(
                continue_button_x,
                button_y,
                button_width,
                button_height
            )
            
            # Draw Continue button
            done_path = QPainterPath()
            done_path.addRoundedRect(
                self.done_button_rect.x(), self.done_button_rect.y(),
                self.done_button_rect.width(), self.done_button_rect.height(),
                button_corner_radius, button_corner_radius
            )
            
            # Continue button color (green when hovered, darker green otherwise)
            if self.done_hovered:
                done_bg_color = QColor(76, 175, 80, 255)  # Bright green
            else:
                done_bg_color = QColor(56, 142, 60, 255)  # Darker green
            painter.fillPath(done_path, done_bg_color)
            
            # Continue button border
            done_border_color = QColor(255, 255, 255, 120)
            pen = painter.pen()
            pen.setColor(done_border_color)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawPath(done_path)
            
            # Continue button text
            continue_text_x = continue_button_x + (button_width - continue_text_width) // 2
            continue_text_y = button_y + button_font_metrics.ascent() + (button_height - button_font_metrics.height()) // 2
            painter.setPen(QColor(255, 255, 255, 255))
            painter.drawText(continue_text_x, continue_text_y, "Continue")
            
            # Exit button (secondary, gray)
            exit_button_x = continue_button_x + button_width + button_spacing
            self.cancel_button_rect = QRect(
                exit_button_x,
                button_y,
                button_width,
                button_height
            )
            
            # Draw Exit button
            cancel_path = QPainterPath()
            cancel_path.addRoundedRect(
                self.cancel_button_rect.x(), self.cancel_button_rect.y(),
                self.cancel_button_rect.width(), self.cancel_button_rect.height(),
                button_corner_radius, button_corner_radius
            )
            
            # Exit button color (lighter gray when hovered)
            if self.cancel_hovered:
                cancel_bg_color = QColor(97, 97, 97, 255)  # Lighter gray
            else:
                cancel_bg_color = QColor(66, 66, 66, 255)  # Darker gray
            painter.fillPath(cancel_path, cancel_bg_color)
            
            # Exit button border
            cancel_border_color = QColor(255, 255, 255, 100)
            pen.setColor(cancel_border_color)
            painter.setPen(pen)
            painter.drawPath(cancel_path)
            
            # Exit button text
            exit_text_x = exit_button_x + (button_width - button_font_metrics.horizontalAdvance("Exit")) // 2
            exit_text_y = button_y + button_font_metrics.ascent() + (button_height - button_font_metrics.height()) // 2
            painter.setPen(QColor(255, 255, 255, 255))
            painter.drawText(exit_text_x, exit_text_y, "Exit")
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events - close on Escape."""
        if event.key() == Qt.Key.Key_Escape:
            self.button_result = 'cancel'  # Treat Escape as cancel
            self.close()
        super().keyPressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse movement for button hover states."""
        if self.done_button_rect and self.done_button_rect.contains(event.pos()):
            if not self.done_hovered:
                self.done_hovered = True
                self.update()
        else:
            if self.done_hovered:
                self.done_hovered = False
                self.update()
        
        if self.cancel_button_rect and self.cancel_button_rect.contains(event.pos()):
            if not self.cancel_hovered:
                self.cancel_hovered = True
                self.update()
        else:
            if self.cancel_hovered:
                self.cancel_hovered = False
                self.update()
        
        super().mouseMoveEvent(event)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse clicks on buttons and overlay."""
        # Check if click is on Continue button
        if self.done_button_rect and self.done_button_rect.contains(event.pos()):
            self.button_result = 'done'
            self.close()
            return
        
        # Check if click is on Exit button
        if self.cancel_button_rect and self.cancel_button_rect.contains(event.pos()):
            self.button_result = 'cancel'
            self.close()
            return
        
        # Check if click is in the text/button area (to the right of bounding box)
        # We want clicks in this area to be handled, but not close the overlay
        # For all other clicks, pass them through to underlying windows
        # Don't close the overlay on outside clicks - let user use buttons or Escape
        
        super().mousePressEvent(event)


def show_overlay(x, y, width, height, text=""):
    """
    Show overlay and return button result.
    
    Args:
        x: X coordinate of bounding box
        y: Y coordinate of bounding box
        width: Width of bounding box
        height: Height of bounding box
        text: Text instructions to display
        
    Returns:
        'done' if Continue button was clicked, 'cancel' if Exit button was clicked, None if closed otherwise
    """
    # Check if QApplication already exists
    app = QApplication.instance()
    if app is None:
        # Create new QApplication if it doesn't exist
        app = QApplication(sys.argv)
    
    # Create overlay window
    window = OverlayWindow(x, y, width, height, text)
    
    # Get screen geometry and set window to cover entire screen
    screen = app.primaryScreen().geometry()
    window.setGeometry(screen)
    
    window.show()
    window.raise_()
    # Don't activate or focus - we want it to stay on top but not steal focus
    
    # Force window to front on macOS to appear above dock
    if sys.platform == 'darwin':
        # Ensure window stays on top
        window.setWindowFlags(
            window.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
        )
        window.show()
        window.raise_()
    
    # Make sure character is on top
    if window.character_label:
        window.character_label.raise_()
    
    # Use a local event loop to wait for window to close
    from PyQt5.QtCore import QEventLoop, QTimer
    loop = QEventLoop()
    
    # Keep window on top even when other windows are activated
    # Use a timer to periodically ensure it stays on top
    def keep_on_top():
        if window.isVisible():
            window.raise_()
            window.setWindowFlags(
                window.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
            )
            window.show()
    
    # Set up a timer to keep window on top
    keep_top_timer = QTimer()
    keep_top_timer.timeout.connect(keep_on_top)
    keep_top_timer.start(100)  # Check every 100ms
    
    def check_closed():
        if not window.isVisible():
            keep_top_timer.stop()
            loop.quit()
    
    # Check periodically if window is closed
    close_timer = QTimer()
    close_timer.timeout.connect(check_closed)
    close_timer.start(50)  # Check every 50ms
    
    # Also connect to close event
    def on_destroyed():
        keep_top_timer.stop()
        close_timer.stop()
        loop.quit()
    
    window.destroyed.connect(on_destroyed)
    
    # Run local event loop
    loop.exec()
    
    keep_top_timer.stop()
    close_timer.stop()
    
    return window.button_result


def main():
    parser = argparse.ArgumentParser(
        description='Create a screen overlay highlighting a bounding box area'
    )
    parser.add_argument('x', type=int, help='X coordinate of bounding box')
    parser.add_argument('y', type=int, help='Y coordinate of bounding box')
    parser.add_argument('width', type=int, help='Width of bounding box')
    parser.add_argument('height', type=int, help='Height of bounding box')
    parser.add_argument('--text', type=str, default='Lorem ipsum dolor sit amet',
                        help='Text instructions to display next to the bounding box')
    
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    
    # Create overlay window
    window = OverlayWindow(args.x, args.y, args.width, args.height, args.text)
    
    # Get screen geometry and set window to cover entire screen
    screen = app.primaryScreen().geometry()
    window.setGeometry(screen)
    
    window.show()
    window.raise_()
    # Don't activate or focus - we want it to stay on top but not steal focus
    
    # Force window to front on macOS to appear above dock
    if sys.platform == 'darwin':
        # Ensure window stays on top
        window.setWindowFlags(
            window.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
        )
        window.show()
        window.raise_()
    
    # Make sure character is on top
    if window.character_label:
        window.character_label.raise_()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

