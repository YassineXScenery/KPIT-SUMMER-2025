from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QTextEdit, 
    QVBoxLayout, QHBoxLayout, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QBrush, QColor, 
    QRadialGradient, QLinearGradient
)
from datetime import datetime
import db
import network

class CarLampWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(250, 250)
        self.on = False
        self.glow_intensity = 0
        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self.update_glow)
        self.glow_timer.start(50)

    def set_state(self, on):
        self.on = on
        self.glow_intensity = 100 if on else 0
        self.update()

    def update_glow(self):
        if self.on and self.glow_intensity < 100:
            self.glow_intensity += 5
        elif not self.on and self.glow_intensity > 0:
            self.glow_intensity -= 5
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        width = self.width()
        height = self.height()
        center_x = width // 2
        center_y = height // 2
        lamp_radius = int(min(width, height) * 0.4)
        
        # Lamp housing
        housing_gradient = QLinearGradient(0, 0, 0, height)
        housing_gradient.setColorAt(0, QColor(80, 80, 90))
        housing_gradient.setColorAt(1, QColor(40, 40, 50))
        painter.setBrush(QBrush(housing_gradient))
        painter.setPen(QColor(30, 30, 40))
        housing_radius = int(lamp_radius * 1.1)
        painter.drawEllipse(center_x - housing_radius, center_y - housing_radius, 
                          housing_radius * 2, housing_radius * 2)
        
        # Lamp lens
        lens_gradient = QRadialGradient(center_x, center_y, lamp_radius)
        lens_gradient.setColorAt(0, QColor(180, 180, 200, 150))
        lens_gradient.setColorAt(1, QColor(50, 50, 70, 150))
        painter.setBrush(QBrush(lens_gradient))
        painter.setPen(QColor(100, 100, 120, 180))
        painter.drawEllipse(center_x - lamp_radius, center_y - lamp_radius, 
                          lamp_radius * 2, lamp_radius * 2)
        
        # Glow effect
        if self.glow_intensity > 0:
            glow_radius = int(lamp_radius * (1 + self.glow_intensity / 200))
            glow_gradient = QRadialGradient(center_x, center_y, glow_radius)
            glow_gradient.setColorAt(0, QColor(255, 230, 180, int(200 * self.glow_intensity / 100)))
            glow_gradient.setColorAt(1, QColor(255, 100, 0, 0))
            painter.setBrush(QBrush(glow_gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center_x - glow_radius, center_y - glow_radius, 
                              glow_radius * 2, glow_radius * 2)

class PhysicalButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumSize(120, 120)
        self.setStyleSheet("""
            QPushButton {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.7,
                    stop:0 #505050, stop:0.6 #303030, stop:0.7 #202020);
                border: 3px solid #101010;
                border-radius: 60px;
                color: #DDD;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:pressed {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.7,
                    stop:0 #303030, stop:0.6 #202020, stop:0.7 #101010);
                padding-top: 5px;
                padding-left: 5px;
            }
        """)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Car Lamp Control Panel")
        self.setStyleSheet("""
            QWidget { background-color: #1a1a2e; color: #e6e6e6; }
            QTextEdit {
                background-color: #16213e;
                border: 1px solid #0f3460;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        # Widgets
        self.lamp = CarLampWidget()
        self.toggle_btn = PhysicalButton("TOGGLE\nLAMP")
        self.status_label = QLabel("LAMP IS OFF")
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        
        # Current states
        self.current_led_state = 'off'
        self.current_button_state = 'not pressed'
        self.last_db_change = None
        
        # Database change watcher (replaces WebSocket)
        self.db_watcher = network.DatabaseWatcher(db_config={
            'host': '10.20.0.2',
            'user': 'user',
            'password': '1234',
            'database': 'iot_system'
        })
        self.db_watcher.update_received.connect(self.handle_db_change)
        self.db_watcher.start()
        
        # Fallback polling timer (5 seconds)
        self.poll_timer = QTimer()
        self.poll_timer.setInterval(5000)
        self.poll_timer.timeout.connect(self.check_for_updates)
        self.poll_timer.start()
        
        # Layout
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        control_layout.addWidget(self.lamp)
        control_layout.addWidget(self.toggle_btn)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(control_frame)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(QLabel("Activity Log:"))
        main_layout.addWidget(self.log_box)
        self.setLayout(main_layout)
        
        # Events
        self.toggle_btn.clicked.connect(self.toggle_led)
        self.log("Application started")
        
        # Initial state load
        self.load_initial_state()

    def load_initial_state(self):
        """Load initial state from database"""
        led_state, button_state, last_change = db.get_current_states()
        if led_state is not None:
            self.current_led_state = led_state
            self.current_button_state = button_state
            self.last_db_change = last_change
            self.update_ui()
            self.log("Initial state loaded")

    def handle_db_change(self, signal, value):
        """Handle changes from MySQL trigger"""
        if signal == 'led':
            self.current_led_state = value
            self.lamp.set_state(value == 'on')
        elif signal == 'button':
            self.current_button_state = value
            
        self.update_ui()
        self.log(f"Real-time change: {signal}={value}")

    def check_for_updates(self):
        """Fallback polling method"""
        try:
            last_change = db.get_last_update_time()
            if last_change == self.last_db_change:
                return
                
            led_state, button_state, last_change = db.get_current_states()
            if led_state is None:
                return
                
            if (led_state != self.current_led_state or 
                button_state != self.current_button_state):
                self.current_led_state = led_state
                self.current_button_state = button_state
                self.last_db_change = last_change
                self.update_ui()
                self.log(f"Polling update: LED={led_state}, Button={button_state}")
                
        except Exception as e:
            self.log(f"Poll error: {str(e)}")

    def toggle_led(self):
        """Toggle LED state and update database"""
        new_led = 'on' if self.current_led_state == 'off' else 'off'
        new_button = 'pressed' if self.current_button_state == 'not pressed' else 'not pressed'
        
        if db.update_states(new_led, new_button):
            self.current_led_state = new_led
            self.current_button_state = new_button
            self.update_ui()
            network.send_udp_message("led1_toggle", '1' if new_led == 'on' else '0')
            self.log(f"LED toggled to {new_led}")
        else:
            self.log("Error updating states")

    def log(self, message):
        """Add timestamped message to log"""
        now = datetime.now().strftime('%H:%M:%S')
        self.log_box.append(f"[{now}] {message}")

    def update_ui(self):
        """Update all UI elements based on current state"""
        # Update lamp
        self.lamp.set_state(self.current_led_state == 'on')
        self.status_label.setText(f"LAMP IS {self.current_led_state.upper()}")
        
        # Update button style
        button_style = """
            QPushButton {{
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.7,
                    stop:0 {color1}, stop:0.6 {color2}, stop:0.7 {color3});
                border: 3px solid #101010;
                border-radius: 60px;
                color: #DDD;
                font-weight: bold;
                font-size: 18px;
                padding: {padding};
            }}
        """
        
        if self.current_button_state == 'pressed':
            style = button_style.format(
                color1="#303030", color2="#202020", color3="#101010",
                padding="5px 0px 0px 5px"
            )
        else:
            style = button_style.format(
                color1="#505050", color2="#303030", color3="#202020",
                padding="0px"
            )
        
        self.toggle_btn.setStyleSheet(style)

    def closeEvent(self, event):
        """Cleanup on window close"""
        self.db_watcher.stop()
        super().closeEvent(event)