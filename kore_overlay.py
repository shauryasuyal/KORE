import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit, QTextEdit
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal, QEvent, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QPolygonF, QCursor, QPainterPath, QKeySequence

def lerp(start, end, factor):
    return start + (end - start) * factor

class KoreOverlay(QWidget):
    # Signals for interaction
    single_click = pyqtSignal()
    double_click = pyqtSignal()
    voice_hotkey = pyqtSignal()
    text_command = pyqtSignal(str)  # New signal for text commands
    
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
        
        # Animation pulse for listening - simplified
        self.pulse_counter = 0
        
        # Thought bubble
        self.current_thought = ""
        self.thought_display_timer = 0
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16) 
        
        self.blink_counter = 0
        self.next_blink = 180
        
        # Sprite positioning - MOVED TO RIGHT SIDE AND MADE SMALLER
        self.sprite_scale = 2.0  # Reduced from 3.0
        self.sprite_x = 0  # Will be calculated based on window width (right side)
        self.sprite_y = 0  # Will be calculated based on window height
        self.clickable_rect = QRectF()
        
        # Track Shift key state for hotkey
        self.shift_pressed = False
        
        # Text input box
        self.text_input = QLineEdit(self)
        self.text_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(30, 41, 59, 230);
                color: white;
                border: 3px solid rgb(148, 163, 184);
                border-radius: 15px;
                padding: 10px 15px;
                font-family: 'Consolas';
                font-size: 14px;
                font-weight: bold;
            }
            QLineEdit:focus {
                border: 3px solid rgb(34, 197, 94);
            }
        """)
        self.text_input.setPlaceholderText("Type your command here...")
        self.text_input.hide()
        self.text_input.returnPressed.connect(self.on_text_submit)
        
        # Install event filter
        self.installEventFilter(self)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def eventFilter(self, obj, event):
        """Filter to catch keyboard events"""
        if event.type() == QEvent.Type.KeyPress:
            # Check for Shift+Enter for voice
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    print("   [Overlay] Shift+Enter pressed!")
                    self.voice_hotkey.emit()
                    return True
            # ESC to close text input
            elif event.key() == Qt.Key.Key_Escape:
                if self.text_input.isVisible():
                    self.text_input.hide()
                    self.text_input.clear()
                    return True
        return super().eventFilter(obj, event)

    def update_animation(self):
        # Update sprite position based on window size - RIGHT SIDE
        self.sprite_x = self.width() - 180 * self.sprite_scale  # Right side with padding
        self.sprite_y = self.height() - 200  # Bottom with padding
        
        # Update text input position if visible
        if self.text_input.isVisible():
            input_width = 400
            input_height = 50
            self.text_input.setGeometry(
                int(self.sprite_x - input_width - 20),
                int(self.sprite_y + 50),
                input_width,
                input_height
            )
        
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
        
        # Thought bubble timer
        if self.thought_display_timer > 0:
            self.thought_display_timer -= 1
            if self.thought_display_timer == 0:
                self.current_thought = ""
        
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
    
    def show_thought(self, text, duration=180):
        """Display a thought bubble above the sprite"""
        self.current_thought = text
        self.thought_display_timer = duration  # frames (about 3 seconds at 60fps)
    
    def show_text_input(self):
        """Show the text input box"""
        self.text_input.show()
        self.text_input.setFocus()
        self.text_input.clear()
    
    def on_text_submit(self):
        """Handle text input submission"""
        text = self.text_input.text().strip()
        if text:
            print(f"   [Overlay] Text command: {text}")
            self.text_command.emit(text)
            self.text_input.clear()
            self.text_input.hide()

    def mousePressEvent(self, event):
        """Handle mouse clicks on the sprite"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = QPointF(event.pos())
            if self.clickable_rect.contains(pos):
                print("   [Overlay] Sprite clicked!")
                self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    
    def mouseReleaseEvent(self, event):
        """Reset cursor on release and show text input on single click"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = QPointF(event.pos())
            if self.clickable_rect.contains(pos):
                # Single click - show text input
                self.show_text_input()
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
    
    def mouseDoubleClickEvent(self, event):
        """Handle double clicks - activate voice mode"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = QPointF(event.pos())
            if self.clickable_rect.contains(pos):
                print("   [Overlay] Sprite double-clicked! Activating voice mode...")
                self.double_click.emit()
                # Hide text input if visible
                if self.text_input.isVisible():
                    self.text_input.hide()
    
    def mouseMoveEvent(self, event):
        """Change cursor when hovering over sprite"""
        pos = QPointF(event.pos())
        if self.clickable_rect.contains(pos):
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fill background with transparent
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        # Draw arm
        arm_pen = QPen(QColor(0, 255, 255, 200))
        arm_pen.setWidth(12)
        painter.setPen(arm_pen)
        painter.drawLine(self.width(), self.height(), int(self.hand_pos.x()), int(self.hand_pos.y()))

        # Draw hand
        painter.setBrush(QBrush(QColor(0, 255, 255, 255)))
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawEllipse(self.hand_pos, 50, 50)
        
        # Draw thought bubble BEFORE sprite (so it appears above)
        if self.current_thought:
            self.draw_thought_bubble(painter)
        
        # Draw minimal listening indicator
        if self.is_listening:
            self.draw_minimal_listening_indicator(painter)
        
        # Draw sprite
        self.draw_sprite(painter)

    def draw_minimal_listening_indicator(self, painter):
        """Draw minimal glowing microphone icon when listening"""
        center_x = self.sprite_x + 70 * self.sprite_scale
        center_y = self.sprite_y - 100
        
        # Pulse effect
        pulse = abs((self.pulse_counter % 40) - 20) / 20.0  # 0 to 1 and back
        
        # Microphone icon
        mic_size = 25 + pulse * 8
        glow_alpha = int(100 + pulse * 155)
        
        # Glow effect
        painter.setPen(QPen(QColor(34, 197, 94, glow_alpha), 8))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(center_x, center_y), mic_size + 10, mic_size + 10)
        
        # Microphone body
        painter.setBrush(QBrush(QColor(34, 197, 94, 255)))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawEllipse(QPointF(center_x, center_y - 5), 12, 18)
        
        # Microphone stand
        painter.drawRect(int(center_x - 3), int(center_y + 13), 6, 8)
        painter.drawRect(int(center_x - 8), int(center_y + 21), 16, 3)
        
        # Sound waves
        for i in range(3):
            wave_dist = 30 + i * 12 + pulse * 8
            wave_alpha = int(200 - i * 50 - pulse * 50)
            painter.setPen(QPen(QColor(34, 197, 94, wave_alpha), 2))
            painter.drawArc(int(center_x - wave_dist), int(center_y - wave_dist), 
                          int(wave_dist * 2), int(wave_dist * 2), 45 * 16, 90 * 16)
            painter.drawArc(int(center_x - wave_dist), int(center_y - wave_dist), 
                          int(wave_dist * 2), int(wave_dist * 2), 225 * 16, 90 * 16)

    def draw_thought_bubble(self, painter):
        """Draw thought bubble above the sprite"""
        bubble_x = self.sprite_x - 50
        bubble_y = self.sprite_y - 180 * self.sprite_scale
        
        # Measure text
        painter.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        text_rect = painter.fontMetrics().boundingRect(
            0, 0, 350, 200,
            Qt.TextFlag.TextWordWrap,
            self.current_thought
        )
        
        bubble_width = max(text_rect.width() + 40, 200)
        bubble_height = text_rect.height() + 30
        
        # Draw thought bubble background
        painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
        painter.setPen(QPen(QColor(100, 116, 139), 3))
        painter.drawRoundedRect(int(bubble_x), int(bubble_y), 
                               int(bubble_width), int(bubble_height), 20, 20)
        
        # Draw thought bubble tail (small circles)
        tail_x = self.sprite_x + 70 * self.sprite_scale
        tail_y = self.sprite_y - 30
        
        painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
        painter.drawEllipse(QPointF(tail_x - 10, tail_y - 20), 8, 8)
        painter.drawEllipse(QPointF(tail_x, tail_y - 35), 12, 12)
        painter.drawEllipse(QPointF(tail_x + 5, tail_y - 55), 15, 15)
        
        # Draw text
        painter.setPen(QPen(QColor(30, 41, 59)))
        painter.drawText(
            int(bubble_x + 20), int(bubble_y + 20),
            int(bubble_width - 40), int(bubble_height - 20),
            Qt.TextFlag.TextWordWrap,
            self.current_thought
        )

    def draw_sprite(self, painter):
        sprite_x = self.sprite_x
        sprite_y = self.sprite_y
        scale = self.sprite_scale
        
        painter.save()
        painter.translate(sprite_x, sprite_y)
        painter.scale(scale, scale)
        
        # LAPTOP SCREEN (top part)
        screen_gradient = QLinearGradient(0, 5, 0, 65)
        screen_gradient.setColorAt(0, QColor(71, 85, 105))
        screen_gradient.setColorAt(1, QColor(51, 65, 85))
        
        painter.setBrush(QBrush(screen_gradient))
        painter.setPen(QPen(QColor(148, 163, 184), 4))
        painter.drawRoundedRect(20, 5, 100, 60, 4, 4)
        
        # Screen bezel
        painter.setBrush(QBrush(QColor(30, 41, 59)))
        painter.setPen(QPen(QColor(100, 116, 139), 2))
        painter.drawRoundedRect(25, 10, 90, 50, 2, 2)
        
        # LAPTOP BASE/KEYBOARD (bottom part)
        body_gradient = QLinearGradient(0, 65, 0, 73)
        body_gradient.setColorAt(0, QColor(203, 213, 225))
        body_gradient.setColorAt(1, QColor(148, 163, 184))
        
        # Top surface of base
        base_top = QPolygonF([QPointF(15, 65), QPointF(20, 68), QPointF(120, 68), QPointF(125, 65)])
        painter.setBrush(QBrush(body_gradient))
        painter.setPen(QPen(QColor(100, 116, 139), 3))
        painter.drawPolygon(base_top)
        
        # Front of base
        base_front = QPolygonF([QPointF(20, 68), QPointF(22, 75), QPointF(118, 75), QPointF(120, 68)])
        painter.setBrush(QBrush(QColor(100, 116, 139)))
        painter.setPen(QPen(QColor(71, 85, 105), 2))
        painter.drawPolygon(base_front)
        
        # Keyboard area
        painter.setBrush(QBrush(QColor(51, 65, 85)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(25, 69, 90, 4)
        
        # Eyes on screen
        is_blinking = self.blink_timer > 0
        eye_scale_y = self.get_eye_scale()
        pupil_size = self.get_pupil_size()
        
        # Left eye
        left_eye_x = 50 + self.look_x
        left_eye_y = 30 + self.look_y
        painter.setBrush(QBrush(QColor(255, 255, 255, 255)))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        
        if is_blinking:
            painter.drawEllipse(int(left_eye_x - 8), int(left_eye_y - 1), 16, 3)
        else:
            painter.drawEllipse(int(left_eye_x - 8), int(left_eye_y - 8 * eye_scale_y), 
                              16, int(16 * eye_scale_y))
            # Pupil
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(left_eye_x + 1 - pupil_size), int(left_eye_y - pupil_size),
                              pupil_size * 2, pupil_size * 2)
            # Shine
            painter.setBrush(QBrush(QColor(255, 255, 255, 255)))
            painter.drawEllipse(int(left_eye_x - 1 - 2), int(left_eye_y - 1.5 - 2), 5, 5)
        
        # Right eye
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
        
        # Mouth
        painter.setPen(QPen(QColor(255, 255, 255), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        mouth_path = self.get_mouth_path()
        painter.drawPath(mouth_path)
        
        # Blush when happy
        if self.emotion == 'happy':
            painter.setBrush(QBrush(QColor(252, 165, 165, 200)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(30, 39, 10, 8)
            painter.drawEllipse(94, 39, 10, 8)
        
        # Emotion decorations
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
        
        # Trackpad
        painter.setBrush(QBrush(QColor(30, 41, 59)))
        painter.setPen(QPen(QColor(100, 116, 139), 1))
        painter.drawRoundedRect(55, 70, 30, 3, 1, 1)
        
        painter.restore()
        
        # Status text - SIMPLIFIED
        status_text = self.get_status_text()
        if status_text:
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
            text_rect = painter.fontMetrics().boundingRect(status_text)
            text_x = int(sprite_x + 70 * scale - text_rect.width() // 2)
            text_y = int(sprite_y + 200)
            
            # Background for text
            painter.setBrush(QBrush(QColor(30, 41, 59, 200)))
            painter.setPen(QPen(QColor(148, 163, 184), 2))
            painter.drawRoundedRect(text_x - 10, text_y - 20, text_rect.width() + 20, 30, 15, 15)
            
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
            return 1.2
        return 1.0
    
    def get_pupil_size(self):
        if self.emotion == 'thinking':
            return 5
        elif self.emotion == 'happy':
            return 4
        elif self.emotion == 'sad':
            return 6
        elif self.is_listening:
            return 3
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
        # Don't show status text when there's a thought bubble
        if self.current_thought:
            return ""
        
        if self.is_listening:
            return 'LISTENING...'
        elif self.is_speaking:
            return 'SPEAKING...'
        elif self.emotion == 'thinking':
            return 'THINKING...'
        elif self.emotion == 'happy':
            return 'SUCCESS!'
        elif self.emotion == 'sad':
            return 'FAILED'
        return 'Click: Chat | Double-click: Voice'
