import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal, QEvent
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QPolygonF, QCursor, QPainterPath, QKeySequence

def lerp(start, end, factor):
    return start + (end - start) * factor

class KoreOverlay(QWidget):
    # Signals for interaction
    single_click = pyqtSignal()
    double_click = pyqtSignal()
    voice_hotkey = pyqtSignal()  # New signal for Shift+Enter
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Kore Overlay")
        
        # CRITICAL: These flags make the window stay on top and be transparent
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        
        # Make background transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        
        # DON'T set WA_TransparentForMouseEvents - we need clicks!
        
        self.hand_pos = QPointF(100, 900) 
        self.target_pos = QPointF(100, 900)
        
        self.emotion = 'idle'
        self.blink_timer = 0
        self.look_x = 0
        self.look_y = 0
        self.look_target_x = 0
        self.look_target_y = 0
        
        # Voice mode indicator
        self.is_listening = False
        self.is_speaking = False
        
        # Animation pulse for listening
        self.pulse_counter = 0
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16) 
        
        self.blink_counter = 0
        self.next_blink = 180
        
        # Clickable area for the laptop sprite (will be set in paintEvent)
        self.sprite_x = 50
        self.sprite_y = 0  # Will be calculated based on window height
        self.sprite_scale = 3.0  # Made bigger
        self.clickable_rect = QRectF()
        
        # Track Shift key state for hotkey
        self.shift_pressed = False
        
        # Install event filter to catch global key events
        self.installEventFilter(self)
        
        # Make window focusable to receive key events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def eventFilter(self, obj, event):
        """Filter to catch keyboard events"""
        if event.type() == QEvent.Type.KeyPress:
            # Check for Shift+Enter
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    print("   [Overlay] Shift+Enter pressed!")
                    self.voice_hotkey.emit()
                    return True
        return super().eventFilter(obj, event)

    def update_animation(self):
        # Update sprite position based on window size
        self.sprite_y = self.height() - 250
        
        new_x = lerp(self.hand_pos.x(), self.target_pos.x(), 0.1)
        new_y = lerp(self.hand_pos.y(), self.target_pos.y(), 0.1)
        self.hand_pos = QPointF(new_x, new_y)
        
        self.blink_counter += 1
        if self.blink_counter >= self.next_blink:
            self.blink_timer = 10
            self.blink_counter = 0
            self.next_blink = 180 + int((hash(str(self.blink_counter)) % 100))
        
        if self.blink_timer > 0:
            self.blink_timer -= 1
        
        # Pulse animation when listening
        if self.is_listening:
            self.pulse_counter += 1
        
        if self.emotion == 'idle' and not self.is_listening:
            if self.blink_counter % 120 == 0:
                self.look_target_x = (hash(str(self.blink_counter)) % 12 - 6)
                self.look_target_y = (hash(str(self.blink_counter + 1)) % 8 - 4)
        else:
            self.look_target_x = 0
            self.look_target_y = 0
        
        self.look_x = lerp(self.look_x, self.look_target_x, 0.05)
        self.look_y = lerp(self.look_y, self.look_target_y, 0.05)
        
        # Update clickable rect
        self.clickable_rect = QRectF(
            self.sprite_x - 20, 
            self.sprite_y - 80 * self.sprite_scale,
            180 * self.sprite_scale, 
            120 * self.sprite_scale
        )
        
        self.update()

    def set_hand_target(self, x, y):
        self.target_pos = QPointF(float(x), float(y))
    
    def set_emotion(self, emotion_state):
        self.emotion = emotion_state
    
    def set_listening(self, is_listening):
        """Set listening state"""
        self.is_listening = is_listening
        if is_listening:
            self.pulse_counter = 0
    
    def set_speaking(self, is_speaking):
        """Set speaking state"""
        self.is_speaking = is_speaking

    def mousePressEvent(self, event):
        """Handle mouse clicks on the sprite"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = QPointF(event.pos())  # Convert QPoint to QPointF
            if self.clickable_rect.contains(pos):
                print("   [Overlay] Sprite clicked!")
                self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    
    def mouseReleaseEvent(self, event):
        """Reset cursor on release"""
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
    
    def mouseDoubleClickEvent(self, event):
        """Handle double clicks - activate voice mode"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = QPointF(event.pos())  # Convert QPoint to QPointF
            if self.clickable_rect.contains(pos):
                print("   [Overlay] Sprite double-clicked! Activating voice mode...")
                self.double_click.emit()
    
    def mouseMoveEvent(self, event):
        """Change cursor when hovering over sprite"""
        pos = QPointF(event.pos())  # Convert QPoint to QPointF
        if self.clickable_rect.contains(pos):
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fill background with transparent (this is important!)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        # Draw arm with bright visible color
        arm_pen = QPen(QColor(0, 255, 255, 200))  # Increased opacity
        arm_pen.setWidth(12)  # Made thicker
        painter.setPen(arm_pen)
        painter.drawLine(0, self.height(), int(self.hand_pos.x()), int(self.hand_pos.y()))

        # Draw hand - BRIGHT and VISIBLE
        painter.setBrush(QBrush(QColor(0, 255, 255, 255)))  # Fully opaque
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawEllipse(self.hand_pos, 50, 50)
        
        # Draw sprite
        self.draw_sprite(painter)
        
        # Draw listening indicator
        if self.is_listening:
            self.draw_listening_indicator(painter)

    def draw_listening_indicator(self, painter):
        """Draw pulsing ring around sprite when listening"""
        pulse = abs((self.pulse_counter % 60) - 30) / 30.0  # 0 to 1 and back
        
        center_x = self.sprite_x + 70 * self.sprite_scale
        center_y = self.sprite_y
        radius = 100 + pulse * 30
        
        painter.setPen(QPen(QColor(34, 197, 94, int(150 + pulse * 105)), 5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(center_x, center_y), radius, radius)
        
        # Inner ring
        painter.setPen(QPen(QColor(134, 239, 172, int(100 + pulse * 155)), 3))
        painter.drawEllipse(QPointF(center_x, center_y), radius - 15, radius - 15)

    def draw_sprite(self, painter):
        sprite_x = self.sprite_x
        sprite_y = self.sprite_y
        scale = self.sprite_scale
        
        painter.save()
        painter.translate(sprite_x, sprite_y)
        painter.scale(scale, scale)
        
        # Add glow effect when listening - BRIGHTER
        if self.is_listening:
            glow_intensity = abs((self.pulse_counter % 40) - 20) / 20.0
            painter.setPen(QPen(QColor(34, 197, 94, int(100 + glow_intensity * 155)), 12))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(15, 0, 110, 70, 8, 8)
        
        # LAPTOP SCREEN (top part) - MUCH BRIGHTER
        screen_gradient = QLinearGradient(0, 5, 0, 65)
        screen_gradient.setColorAt(0, QColor(71, 85, 105))  # Lighter
        screen_gradient.setColorAt(1, QColor(51, 65, 85))   # Lighter
        
        painter.setBrush(QBrush(screen_gradient))
        painter.setPen(QPen(QColor(148, 163, 184), 4))  # Bright border
        painter.drawRoundedRect(20, 5, 100, 60, 4, 4)
        
        # Screen bezel - VISIBLE
        painter.setBrush(QBrush(QColor(30, 41, 59)))
        painter.setPen(QPen(QColor(100, 116, 139), 2))
        painter.drawRoundedRect(25, 10, 90, 50, 2, 2)
        
        # LAPTOP BASE/KEYBOARD (bottom part) - BRIGHTER
        body_gradient = QLinearGradient(0, 65, 0, 73)
        body_gradient.setColorAt(0, QColor(203, 213, 225))  # Much lighter
        body_gradient.setColorAt(1, QColor(148, 163, 184))  # Much lighter
        
        # Top surface of base
        base_top = QPolygonF([QPointF(15, 65), QPointF(20, 68), QPointF(120, 68), QPointF(125, 65)])
        painter.setBrush(QBrush(body_gradient))
        painter.setPen(QPen(QColor(100, 116, 139), 3))
        painter.drawPolygon(base_top)
        
        # Front of base - VISIBLE
        base_front = QPolygonF([QPointF(20, 68), QPointF(22, 75), QPointF(118, 75), QPointF(120, 68)])
        painter.setBrush(QBrush(QColor(100, 116, 139)))
        painter.setPen(QPen(QColor(71, 85, 105), 2))
        painter.drawPolygon(base_front)
        
        # Keyboard area - BRIGHT
        painter.setBrush(QBrush(QColor(51, 65, 85)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(25, 69, 90, 4)
        
        # Eyes on screen - BRIGHT WHITE
        is_blinking = self.blink_timer > 0
        eye_scale_y = self.get_eye_scale()
        pupil_size = self.get_pupil_size()
        
        # Left eye - BRIGHT
        left_eye_x = 50 + self.look_x
        left_eye_y = 30 + self.look_y
        painter.setBrush(QBrush(QColor(255, 255, 255, 255)))  # Fully opaque
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        
        if is_blinking:
            painter.drawEllipse(int(left_eye_x - 8), int(left_eye_y - 1), 16, 3)
        else:
            painter.drawEllipse(int(left_eye_x - 8), int(left_eye_y - 8 * eye_scale_y), 
                              16, int(16 * eye_scale_y))
            # Pupil - BLACK
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(left_eye_x + 1 - pupil_size), int(left_eye_y - pupil_size),
                              pupil_size * 2, pupil_size * 2)
            # Shine - BRIGHT
            painter.setBrush(QBrush(QColor(255, 255, 255, 255)))
            painter.drawEllipse(int(left_eye_x - 1 - 2), int(left_eye_y - 1.5 - 2), 5, 5)
        
        # Right eye - BRIGHT
        right_eye_x = 90 + self.look_x
        right_eye_y = 30 + self.look_y
        painter.setBrush(QBrush(QColor(255, 255, 255, 255)))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        
        if is_blinking:
            painter.drawEllipse(int(right_eye_x - 8), int(right_eye_y - 1), 16, 3)
        else:
            painter.drawEllipse(int(right_eye_x - 8), int(right_eye_y - 8 * eye_scale_y),
                              16, int(16 * eye_scale_y))
            # Pupil
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(right_eye_x + 1 - pupil_size), int(right_eye_y - pupil_size),
                              pupil_size * 2, pupil_size * 2)
            # Shine
            painter.setBrush(QBrush(QColor(255, 255, 255, 255)))
            painter.drawEllipse(int(right_eye_x - 1 - 2), int(right_eye_y - 1.5 - 2), 5, 5)
        
        # Mouth - BRIGHT
        painter.setPen(QPen(QColor(255, 255, 255), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        mouth_path = self.get_mouth_path()
        painter.drawPath(mouth_path)
        
        # Blush when happy - BRIGHT
        if self.emotion == 'happy':
            painter.setBrush(QBrush(QColor(252, 165, 165, 200)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(30, 39, 10, 8)
            painter.drawEllipse(94, 39, 10, 8)
        
        # Emotion decorations - BRIGHTER
        if self.emotion == 'thinking':
            painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
            painter.setPen(Qt.PenStyle.NoPen)
            offset = (self.blink_counter % 30) / 30.0 * 3
            painter.drawEllipse(int(115 - offset), 20, 5, 5)
            painter.drawEllipse(int(118 - offset * 0.7), 15, 6, 6)
            painter.drawEllipse(int(122 - offset * 0.5), 11, 8, 8)
        
        elif self.emotion == 'happy':
            painter.setBrush(QBrush(QColor(251, 191, 36, 255)))
            angle = (self.blink_counter * 6) % 360
            painter.save()
            painter.translate(15, 25)
            painter.rotate(angle)
            painter.drawPolygon(QPolygonF([QPointF(0, -4), QPointF(1.5, 0), QPointF(0, 4), QPointF(-1.5, 0)]))
            painter.restore()
            
            painter.save()
            painter.translate(125, 50)
            painter.rotate(angle * 1.5)
            painter.drawPolygon(QPolygonF([QPointF(0, -4), QPointF(1.5, 0), QPointF(0, 4), QPointF(-1.5, 0)]))
            painter.restore()
        
        elif self.emotion == 'sad':
            tear_offset = (self.blink_counter % 60) / 60.0 * 8
            painter.setBrush(QBrush(QColor(96, 165, 250, 220)))
            painter.setPen(Qt.PenStyle.NoPen)
            if tear_offset < 7:
                painter.drawEllipse(int(48), int(38 + tear_offset), 5, 10)
                painter.drawEllipse(int(92), int(38 + tear_offset + 1), 5, 10)
        
        # Microphone icon when listening - BRIGHT
        if self.is_listening:
            painter.setBrush(QBrush(QColor(34, 197, 94, 255)))
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawEllipse(67, 47, 6, 9)
            painter.drawRect(68, 56, 4, 4)
            painter.drawRect(66, 60, 8, 2)
        
        # Trackpad - VISIBLE
        painter.setBrush(QBrush(QColor(30, 41, 59)))
        painter.setPen(QPen(QColor(100, 116, 139), 1))
        painter.drawRoundedRect(55, 70, 30, 3, 1, 1)
        
        painter.restore()
        
        # Status text - MUCH BRIGHTER
        status_text = self.get_status_text()
        painter.setPen(QPen(QColor(255, 255, 255)))  # Pure white
        painter.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        text_rect = painter.fontMetrics().boundingRect(status_text)
        text_x = sprite_x + 175 - text_rect.width() // 2
        text_y = sprite_y + 320
        
        # Bright background for text
        painter.setBrush(QBrush(QColor(30, 41, 59, 230)))
        painter.setPen(QPen(QColor(148, 163, 184), 3))
        painter.drawRoundedRect(text_x - 15, text_y - 25, text_rect.width() + 30, 40, 20, 20)
        
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.drawText(text_x, text_y, status_text)
    
    def get_eye_scale(self):
        if self.emotion == 'thinking':
            return 0.7
        elif self.emotion == 'happy':
            return 0.5
        elif self.emotion == 'sad':
            return 1.0
        elif self.is_listening:
            return 1.2  # Wide eyes when listening
        return 1.0
    
    def get_pupil_size(self):
        if self.emotion == 'thinking':
            return 5
        elif self.emotion == 'happy':
            return 4
        elif self.emotion == 'sad':
            return 6
        elif self.is_listening:
            return 3  # Small pupils when focused
        return 5
    
    def get_mouth_path(self):
        path = QPainterPath()
        
        if self.emotion == 'happy':
            path.moveTo(60, 52)
            path.quadTo(70, 58, 80, 52)
        elif self.emotion == 'sad':
            path.moveTo(60, 55)
            path.quadTo(70, 50, 80, 55)
        elif self.emotion == 'thinking':
            path.moveTo(63, 54)
            path.lineTo(77, 54)
        elif self.is_listening:
            # O shape for listening
            path.addEllipse(66, 51, 8, 8)
        elif self.is_speaking:
            # Animated mouth for speaking
            amplitude = abs((self.blink_counter % 20) - 10) / 10.0
            path.moveTo(63, 54)
            path.quadTo(70, 54 + amplitude * 3, 77, 54)
        else:
            path.moveTo(63, 54)
            path.quadTo(70, 56, 77, 54)
        
        return path
    
    def get_status_text(self):
        if self.is_listening:
            return ' LISTENING...'
        elif self.is_speaking:
            return ' SPEAKING...'
        elif self.emotion == 'thinking':
            return ' THINKING...'
        elif self.emotion == 'happy':
            return ' SUCCESS!'
        elif self.emotion == 'sad':
            return ' FAILED'
        return ' READY (Shift+Enter or Double-click!)'