import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QTextEdit,
    QVBoxLayout, QHBoxLayout, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QBrush, QColor,
    QRadialGradient, QLinearGradient, QMovie
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

class ManualWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        print("Initializing ManualWindow")
        self.setWindowTitle("Car Lamp Control Panel")
        self.connection_attempts = 0
        self.max_connection_attempts = 5
        self.connection_successful = False

        # Initialize default states
        self.current_led_state = 'off'
        self.current_button_state = 'not pressed'
        self.last_db_change = None

        # Setup UI first
        self.init_ui()

        # Start connection attempts in background
        self.log("Application started")
        QTimer.singleShot(100, self.attempt_connection)

    def init_ui(self):
        # Background label setup
        self.background = QLabel(self)
        self.background.setAlignment(Qt.AlignCenter)
        self.background.setScaledContents(True)

        # Get assets path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        gif_path = os.path.join(project_root, "assets", "Backgroundmanual.gif")

        # Check for GIF with case-insensitive variation
        if not os.path.exists(gif_path):
            alt_gif_path = os.path.join(project_root, "assets", "backgroundmanual.gif")
            if os.path.exists(alt_gif_path):
                gif_path = alt_gif_path

        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            self.background.setMovie(self.movie)
            self.movie.start()
            self.setStyleSheet("""
                QWidget { background-color: transparent; color: #e6e6e6; }
                QTextEdit {
                    background-color: rgba(90, 90, 90, 180);
                    border: 1px solid #0f3460;
                    border-radius: 8px;
                    padding: 8px;
                }
                QLabel#background { background-color: transparent; }
            """)
        else:
            self.setStyleSheet("""
                QWidget { background-color: #1a1a2e; color: #e6e6e6; }
                QTextEdit {
                    background-color: rgba(90, 90, 90, 180);
                    border: 1px solid #0f3460;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)

        # UI Elements
        self.lamp = CarLampWidget()
        self.toggle_btn = PhysicalButton("TOGGLE\nLAMP")
        self.status_label = QLabel("LAMP IS OFF")
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        
        # Improved Back button (green and positioned top-right)
        self.back_btn = QPushButton("← Back to Main")
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 80, 0, 0.7);
                border: 2px solid #00aa00;
                border-radius: 5px;
                color: #00ff00;
                padding: 5px 10px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: rgba(0, 100, 0, 0.8);
                border: 2px solid #00ff00;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: rgba(0, 120, 0, 0.9);
                border: 2px solid #00ff00;
                padding: 6px 10px 4px 10px;
            }
        """)
        self.back_btn.clicked.connect(self.go_back)

        # Layout
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        control_layout.addWidget(self.lamp)
        control_layout.addWidget(self.toggle_btn)

        # Top bar layout for back button
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        top_bar.addWidget(self.back_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_bar)  # Add top bar first
        main_layout.addWidget(control_frame)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(QLabel("Activity Log:"))
        main_layout.addWidget(self.log_box)
        main_layout.setContentsMargins(20, 10, 20, 20)  # Reduced top margin

        self.setLayout(main_layout)
        self.background.lower()
        self.background.setGeometry(0, 0, self.width(), self.height())

        # Connect signals
        self.toggle_btn.clicked.connect(self.toggle_led)

        # Initialize UI state
        self.update_ui()

    def update_ui(self):
        self.lamp.set_state(self.current_led_state == 'on')
        self.status_label.setText(f"LAMP IS {self.current_led_state.upper()}")
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

    def attempt_connection(self):
        if self.connection_attempts >= self.max_connection_attempts:
            self.log("Max connection attempts reached. Operating in offline mode.")
            return

        self.connection_attempts += 1
        try:
            self.db_watcher = network.DatabaseWatcher(db_config={
                'host': '10.20.0.2',
                'user': 'user',
                'password': '1234',
                'database': 'iot_system'
            })
            self.db_watcher.update_received.connect(self.handle_db_change)
            self.db_watcher.start()
            self.connection_successful = True
            self.log("Database connection established")
            self.load_initial_state()
        except Exception as e:
            self.log(f"Connection attempt {self.connection_attempts} failed: {str(e)}")
            if self.connection_attempts < self.max_connection_attempts:
                QTimer.singleShot(2000, self.attempt_connection)

    def go_back(self):
        """Fixed back button functionality"""
        try:
            # Get the parent directory path
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            
            # Add the project root to Python path
            if project_root not in sys.path:
                sys.path.append(project_root)
            
            # Import WelcomeWindow correctly
            from components.WelcomeWindow import WelcomeWindow
            
            # Close current window and show welcome window
            self.close()
            self.welcome_window = WelcomeWindow()
            self.welcome_window.show()
        except Exception as e:
            self.log(f"Error going back: {str(e)}")
            print(f"Error going back: {str(e)}")

    def load_initial_state(self):
        try:
            led_state, button_state, last_change = db.get_current_states()
            if led_state is not None:
                self.current_led_state = led_state
                self.current_button_state = button_state
                self.last_db_change = last_change
                self.update_ui()
                self.log("Initial state loaded")
        except Exception as e:
            self.log(f"Error loading initial state: {str(e)}")

    def handle_db_change(self, signal, value):
        if signal == 'led':
            self.current_led_state = value
            self.lamp.set_state(value == 'on')
        elif signal == 'button':
            self.current_button_state = value
        self.update_ui()
        self.log(f"Real-time change: {signal}={value}")

    def check_for_updates(self):
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
        new_led = 'on' if self.current_led_state == 'off' else 'off'
        new_button = 'pressed' if self.current_button_state == 'not pressed' else 'not pressed'
        try:
            if self.connection_successful and db.update_states(new_led, new_button):
                self.current_led_state = new_led
                self.current_button_state = new_button
                self.update_ui()
                network.send_udp_message("led1_toggle", '1' if new_led == 'on' else '0')
                self.log(f"LED toggled to {new_led}")
            else:
                # Fallback for offline mode
                self.current_led_state = new_led
                self.current_button_state = new_button
                self.update_ui()
                self.log(f"LED toggled (offline mode): {new_led}")
        except Exception as e:
            self.log(f"Error toggling LED: {str(e)}")

    def log(self, message):
        now = datetime.now().strftime('%H:%M:%S')
        if hasattr(self, 'log_box'):
            self.log_box.append(f"[{now}] {message}")
        else:
            print(f"Log error: log_box not initialized. Message: [{now}] {message}")

    def resizeEvent(self, event):
        self.background.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def closeEvent(self, event):
        if hasattr(self, 'db_watcher') and self.db_watcher is not None:
            self.db_watcher.stop()
        if hasattr(self, 'movie'):
            self.movie.stop()
        super().closeEvent(event)