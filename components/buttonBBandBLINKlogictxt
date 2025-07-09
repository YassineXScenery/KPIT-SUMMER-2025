import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QTextEdit,
    QVBoxLayout, QHBoxLayout, QFrame, QButtonGroup
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QBrush, QColor,
    QRadialGradient, QLinearGradient, QFont, QPixmap
)
from datetime import datetime
import db
import network

class CarLampWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(50, 50)
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
        self.setMinimumSize(100, 100)
        self.setFont(QFont('Arial', 14))
        self.setStyleSheet("""
            QPushButton {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.7,
                    stop:0 #606060, stop:0.6 #404040, stop:0.7 #303030);
                border: 4px solid #151515;
                border-radius: 50px;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:pressed:enabled {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.7,
                    stop:0 #404040, stop:0.6 #303030, stop:0.7 #202020);
                padding-top: 4px;
                padding-left: 4px;
            }
            QPushButton:disabled {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.7,
                    stop:0 #505050, stop:0.6 #404040, stop:0.7 #303030);
                color: #888888;
                border: 4px solid #151515;
                padding: 0px;
            }
        """)

class ManualWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        print("Initializing ManualWindow")
        self.setWindowTitle("Car Lamp Control Panel")
        self.resize(1000, 800)
        
        # Connection settings
        self.connection_attempts = 0
        self.max_connection_attempts = 3
        self.connection_successful = False
        self.offline_mode = False

        # Initialize default states
        self.current_led_state = 'off'
        self.current_button_state = 'not pressed'
        self.current_pwf_state = 'P'
        self.last_db_change = None

        # Setup UI
        self.init_ui()

        # Start connection attempts
        self.log("Application started")
        QTimer.singleShot(100, self.attempt_connection)

        # Setup PWF timer (will be started after successful connection)
        self.pwf_timer = QTimer(self)
        self.pwf_timer.timeout.connect(self.check_pwf_state)

    def init_ui(self):
        # Set dark background
        self.setStyleSheet("""
            QWidget { background-color: #1a1a2e; color: #e6e6e6; }
            QTextEdit {
                background-color: rgba(90, 90, 90, 180);
                border: 2px solid #0f3460;
                border-radius: 10px;
                padding: 10px;
                font-size: 14pt;
            }
            QLabel {
                font-size: 16pt;
                color: #FFFFFF;
            }
        """)

        # UI Elements
        self.left_lamp = CarLampWidget()
        self.right_lamp = CarLampWidget()
        self.toggle_btn = PhysicalButton("TOGGLE\nBUTTON")
        self.status_label = QLabel("LAMPS ARE OFF")
        self.status_label.setFont(QFont('Arial', 16))
        self.log_box = QTextEdit()
        self.log_box.setMinimumHeight(300)
        self.log_box.setFont(QFont('Arial', 14))
        self.log_box.setReadOnly(True)

        # Add car image
        self.car_label = QLabel(self)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        car_path = os.path.join(project_root, "assets", "car.png")
        if os.path.exists(car_path):
            car_pixmap = QPixmap(car_path)
            scaled_pixmap = car_pixmap.scaled(600, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.car_label.setPixmap(scaled_pixmap)
            self.car_label.setAlignment(Qt.AlignCenter)
        else:
            self.car_label.setText("car.png not found")

        # Back button
        self.back_btn = QPushButton("← Back to Main")
        self.back_btn.setMinimumWidth(150)
        self.back_btn.setFont(QFont('Arial', 14))
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 100, 0, 0.8);
                border: 3px solid #00cc00;
                border-radius: 8px;
                color: #00ff00;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 14pt;
            }
            QPushButton:hover {
                background-color: rgba(0, 120, 0, 0.9);
                border: 3px solid #00ff00;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: rgba(0, 140, 0, 1.0);
                border: 3px solid #00ff00;
                padding: 9px 15px 7px 15px;
            }
        """)
        self.back_btn.clicked.connect(self.go_back)

        # PWF buttons
        pwf_button_style = """
            QPushButton {
                background-color: #404040;
                border: 3px solid #151515;
                border-radius: 12px;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 16pt;
                padding: 8px;
                min-width: 80px;
                min-height: 60px;
            }
            QPushButton:checked {
                background-color: #606060;
                border: 3px solid #00ff00;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
            QPushButton:disabled {
                background-color: #505050;
                color: #888888;
                border: 3px solid #151515;
            }
        """

        self.p_btn = QPushButton('P')
        self.p_btn.setCheckable(True)
        self.p_btn.setStyleSheet(pwf_button_style)
        self.p_btn.setEnabled(False)

        self.s_btn = QPushButton('S')
        self.s_btn.setCheckable(True)
        self.s_btn.setStyleSheet(pwf_button_style)
        self.s_btn.setEnabled(False)

        self.w_btn = QPushButton('W')
        self.w_btn.setCheckable(True)
        self.w_btn.setStyleSheet(pwf_button_style)
        self.w_btn.setEnabled(False)

        self.f_btn = QPushButton('F')
        self.f_btn.setCheckable(True)
        self.f_btn.setStyleSheet(pwf_button_style)
        self.f_btn.setEnabled(False)

        self.pwf_group = QButtonGroup()
        self.pwf_group.setExclusive(True)
        self.pwf_group.addButton(self.p_btn)
        self.pwf_group.addButton(self.s_btn)
        self.pwf_group.addButton(self.w_btn)
        self.pwf_group.addButton(self.f_btn)
        self.pwf_group.buttonClicked.connect(self.on_pwf_state_change)

        # Layout
        top_bar = QHBoxLayout()
        pwf_label = QLabel("PWF State:")
        pwf_label.setFont(QFont('Arial', 16))
        top_bar.addWidget(pwf_label)
        top_bar.addWidget(self.p_btn)
        top_bar.addWidget(self.s_btn)
        top_bar.addWidget(self.w_btn)
        top_bar.addWidget(self.f_btn)
        top_bar.addStretch()
        top_bar.addWidget(self.back_btn)
        top_bar.setContentsMargins(10, 10, 10, 10)
        top_bar.setSpacing(15)

        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        control_layout.addWidget(self.toggle_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.car_label, alignment=Qt.AlignCenter)
        lamps_layout = QHBoxLayout()
        lamps_layout.addWidget(self.left_lamp)
        lamps_layout.addSpacing(100)
        lamps_layout.addWidget(self.right_lamp)
        control_layout.addLayout(lamps_layout)
        control_layout.setSpacing(20)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_bar)
        main_layout.addWidget(control_frame)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(QLabel("Activity Log:"))
        main_layout.addWidget(self.log_box)
        main_layout.setContentsMargins(30, 20, 30, 30)
        main_layout.setSpacing(20)

        self.setLayout(main_layout)
        self.toggle_btn.clicked.connect(self.toggle_button)
        self.update_ui()

    def attempt_connection(self):
        if self.connection_attempts >= self.max_connection_attempts:
            self.offline_mode = True
            self.log("Max connection attempts reached. Operating in offline mode.")
            self.update_ui()
            return

        self.connection_attempts += 1
        try:
            # Test basic connection with proper cleanup
            conn = db.get_connection()
            if conn is None:
                raise Exception("Connection object is None")
            
            # Test with simple query and ensure we read all results
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchall()  # Ensure we read all results
            cursor.close()
            conn.close()
            
            # Setup database watcher with proper error handling
            try:
                if hasattr(self, 'db_watcher'):
                    self.db_watcher.stop()
                    
                self.db_watcher = network.DatabaseWatcher(db_config={
                    'host': '10.20.0.2',
                    'user': 'user',
                    'password': '1234',
                    'database': 'iot_system'
                })
                self.db_watcher.update_received.connect(self.handle_db_change)
                self.db_watcher.start()
            except Exception as e:
                self.log(f"DatabaseWatcher initialization failed: {str(e)}")
                raise Exception("DatabaseWatcher failed")
            
            self.connection_successful = True
            self.offline_mode = False
            self.pwf_timer.start(5000)
            self.log("Database connection established")
            self.load_initial_state()
            
            # Enable PWF buttons
            self.p_btn.setEnabled(True)
            self.s_btn.setEnabled(True)
            self.w_btn.setEnabled(True)
            self.f_btn.setEnabled(True)
            
        except Exception as e:
            error_msg = str(e)
            if "1130" in error_msg:
                error_msg = "MySQL server rejected connection from this host"
            elif "Unread result found" in error_msg:
                error_msg = "Connection issue - please restart the application"
            self.log(f"Connection attempt {self.connection_attempts} failed: {error_msg}")
            
            if self.connection_attempts < self.max_connection_attempts:
                retry_delay = 2000 * self.connection_attempts
                QTimer.singleShot(retry_delay, self.attempt_connection)
            else:
                self.offline_mode = True
                self.log("Switching to offline mode")
                self.update_ui()

    def load_initial_state(self):
        try:
            if self.offline_mode:
                self.log("Offline mode - using default states")
                return
                
            led_state, button_state, last_change = db.get_current_states()
            if led_state is not None:
                self.current_led_state = led_state
                self.current_button_state = button_state
                self.last_db_change = last_change
                self.log("Initial state loaded")
            
            # Load PWF state
            conn = db.get_connection()
            if conn is None:
                raise Exception("Could not get connection")
                
            cursor = conn.cursor()
            cursor.execute("SELECT state FROM pwf_state ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            
            if result:
                self.current_pwf_state = result[0]
                if self.current_pwf_state == 'P':
                    self.p_btn.setChecked(True)
                elif self.current_pwf_state == 'S':
                    self.s_btn.setChecked(True)
                elif self.current_pwf_state == 'W':
                    self.w_btn.setChecked(True)
                elif self.current_pwf_state == 'F':
                    self.f_btn.setChecked(True)
            else:
                # Initialize table if empty
                cursor.execute("INSERT INTO pwf_state (state, is_active, timestamp) VALUES (%s, %s, CURRENT_TIMESTAMP)", ('P', 0))
                conn.commit()
                self.current_pwf_state = 'P'
                self.p_btn.setChecked(True)
                
            conn.close()
            self.update_ui()
            
        except Exception as e:
            self.log(f"Error loading initial state: {str(e)}")
            self.offline_mode = True
            self.update_ui()

    def update_ui(self):
        # Update lamps
        self.left_lamp.set_state(self.current_led_state == 'on')
        self.right_lamp.set_state(self.current_led_state == 'on')
        
        # Update status label
        status_text = f"LAMPS ARE {self.current_led_state.upper()} (PWF: {self.current_pwf_state})"
        if self.offline_mode:
            status_text += " [OFFLINE MODE]"
        elif not self.connection_successful:
            status_text += " [CONNECTING...]"
        self.status_label.setText(status_text)
        
        # Update toggle button style
        style = """
            QPushButton {{
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.7,
                    stop:0 {color1}, stop:0.6 {color2}, stop:0.7 {color3});
                border: 4px solid #151515;
                border-radius: 50px;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 14pt;
                padding: {padding};
            }}
        """
        if self.current_button_state == 'pressed':
            style = style.format(
                color1="#404040",
                color2="#303030",
                color3="#202020",
                padding="4px 0px 0px 4px"
            )
        else:
            style = style.format(
                color1="#606060",
                color2="#404040",
                color3="#303030",
                padding="0px"
            )
        self.toggle_btn.setStyleSheet(style)
        self.toggle_btn.setEnabled(True)

    def handle_db_change(self, signal, value):
        if self.offline_mode:
            return
            
        try:
            if signal == 'led':
                if value not in ['on', 'off']:
                    if value in ['blink_slow', 'blink_fast', '0']:
                        value = 'off'
                    else:
                        self.log(f"Unhandled LED value: {value}")
                        return
                self.current_led_state = value
                self.left_lamp.set_state(value == 'on')
                self.right_lamp.set_state(value == 'on')
            elif signal == 'button':
                if value not in ['pressed', 'not pressed']:
                    if value == '1':
                        value = 'pressed'
                    elif value == '0':
                        value = 'not pressed'
                    else:
                        self.log(f"Unhandled button value: {value}")
                        return
                self.current_button_state = value
                
                if self.current_pwf_state in ['W', 'F']:
                    new_led = 'on' if value == 'pressed' else 'off'
                    if new_led != self.current_led_state:
                        self.current_led_state = new_led
                        self.left_lamp.set_state(new_led == 'on')
                        self.right_lamp.set_state(new_led == 'on')
                        if self.connection_successful:
                            try:
                                conn = db.get_connection()
                                cursor = conn.cursor()
                                cursor.execute("INSERT INTO signals_log (signal_name, value, source) VALUES (%s, %s, %s)",
                                              ('led', new_led, 'GUI'))
                                conn.commit()
                                db.update_states(new_led, value)
                                try:
                                    network.send_udp_message("led1_toggle", '1' if new_led == 'on' else '0')
                                    self.log(f"LEDs updated to {new_led} due to button change, UDP sent")
                                except Exception as e:
                                    self.log(f"LEDs updated to {new_led}, but UDP failed: {str(e)}")
                                conn.close()
                            except Exception as e:
                                self.log(f"Error updating LEDs on button change: {str(e)}")
                elif self.current_pwf_state in ['P', 'S'] and self.current_led_state == 'on':
                    self.current_led_state = 'off'
                    self.left_lamp.set_state(False)
                    self.right_lamp.set_state(False)
                    if self.connection_successful:
                        try:
                            conn = db.get_connection()
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO signals_log (signal_name, value, source) VALUES (%s, %s, %s)",
                                          ('led', 'off', 'GUI'))
                            conn.commit()
                            db.update_states('off', value)
                            try:
                                network.send_udp_message("led1_toggle", '0')
                                self.log("LEDs turned off due to P/S state, UDP sent")
                            except Exception as e:
                                self.log(f"LEDs turned off, but UDP failed: {str(e)}")
                            conn.close()
                        except Exception as e:
                            self.log(f"Error forcing LEDs off in P/S: {str(e)}")
            self.update_ui()
            self.log(f"Real-time change: {signal}={value}")
        except Exception as e:
            self.log(f"Error handling DB change: {str(e)}")
            self.connection_successful = False
            self.attempt_connection()

    def toggle_button(self):
        new_button = 'pressed' if self.current_button_state == 'not pressed' else 'not pressed'
        new_led = self.current_led_state
        
        if self.current_pwf_state in ['W', 'F']:
            new_led = 'on' if new_button == 'pressed' else 'off'
        elif self.current_pwf_state in ['P', 'S']:
            new_led = 'off'

        try:
            if not self.offline_mode and self.connection_successful:
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO signals_log (signal_name, value, source) VALUES (%s, %s, %s)",
                              ('button', new_button, 'GUI'))
                if new_led != self.current_led_state:
                    cursor.execute("INSERT INTO signals_log (signal_name, value, source) VALUES (%s, %s, %s)",
                                  ('led', new_led, 'GUI'))
                conn.commit()
                success = db.update_states(new_led, new_button)
                if success:
                    self.current_led_state = new_led
                    self.current_button_state = new_button
                    self.left_lamp.set_state(new_led == 'on')
                    self.right_lamp.set_state(new_led == 'on')
                    try:
                        network.send_udp_message("led1_toggle", '1' if new_led == 'on' else '0')
                        self.log(f"Button toggled to {new_button}, LEDs set to {new_led}, UDP sent")
                    except Exception as e:
                        self.log(f"Button toggled to {new_button}, LEDs set to {new_led}, but UDP failed: {str(e)}")
                else:
                    self.log(f"Failed to update database states with LEDs={new_led}, Button={new_button}")
                    cursor.execute("DELETE FROM signals_log WHERE signal_name IN ('led', 'button') AND timestamp >= NOW() - INTERVAL 1 SECOND")
                    conn.commit()
                    conn.close()
                    return
                conn.close()
            else:
                # Offline mode - just update UI
                self.current_led_state = new_led
                self.current_button_state = new_button
                self.left_lamp.set_state(new_led == 'on')
                self.right_lamp.set_state(new_led == 'on')
                self.log(f"Offline mode - Button toggled to {new_button}, LEDs set to {new_led}")
                
            self.update_ui()
        except Exception as e:
            self.log(f"Error toggling button: {str(e)}")
            try:
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM signals_log WHERE signal_name IN ('led', 'button') AND timestamp >= NOW() - INTERVAL 1 SECOND")
                conn.commit()
                conn.close()
            except Exception as e2:
                self.log(f"Error rolling back signals_log: {str(e2)}")

    def on_pwf_state_change(self):
        checked_button = self.pwf_group.checkedButton()
        if not checked_button:
            return
            
        new_state = checked_button.text()
        
        # Check for invalid transitions (P↔F)
        if (self.current_pwf_state == 'P' and new_state == 'F') or (self.current_pwf_state == 'F' and new_state == 'P'):
            self.log(f"Invalid transition from {self.current_pwf_state} to {new_state}")
            # Revert to current state
            if self.current_pwf_state == 'P':
                self.p_btn.setChecked(True)
            elif self.current_pwf_state == 'S':
                self.s_btn.setChecked(True)
            elif self.current_pwf_state == 'W':
                self.w_btn.setChecked(True)
            elif self.current_pwf_state == 'F':
                self.f_btn.setChecked(True)
            return
        
        if self.offline_mode:
            self.log(f"Offline mode - PWF state changed to {new_state} (not saved)")
            self.current_pwf_state = new_state
            self.update_ui()
            return
            
        try:
            conn = db.get_connection()
            if conn is None:
                raise Exception("Could not get connection")
                
            cursor = conn.cursor()
            
            # Send buttonBB signal based on PWF state
            if new_state == 'P':
                button_value = 'pressed_3'
                led_value = 'NOT BLINK'
            elif new_state == 'S':
                button_value = 'pressed_4'
                led_value = 'NOT BLINK'
            elif new_state == 'W':
                button_value = 'pressed_1'
                led_value = 'BLINK'
            elif new_state == 'F':
                button_value = 'pressed_2'
                led_value = 'BLINK'
            
            # Send buttonBB signal
            cursor.execute("INSERT INTO signals_log (signal_name, value, source) VALUES (%s, %s, %s)",
                          ('buttonBB', button_value, 'GUI'))
            
            # Send LED signal
            cursor.execute("INSERT INTO signals_log (signal_name, value, source) VALUES (%s, %s, %s)",
                          ('led', led_value, 'GUI'))
            
            # Update PWF state
            cursor.execute("SELECT MAX(id) FROM pwf_state")
            max_id = cursor.fetchone()[0]
            if max_id is None:
                cursor.execute("INSERT INTO pwf_state (state, is_active, timestamp) VALUES (%s, %s, CURRENT_TIMESTAMP)", (new_state, 0))
            else:
                cursor.execute("UPDATE pwf_state SET state = %s, is_active = %s, timestamp = CURRENT_TIMESTAMP WHERE id = %s", (new_state, 0, max_id))
            
            conn.commit()
            self.current_pwf_state = new_state
            
            # Update LED state based on new PWF state
            if new_state in ['P', 'S']:
                self.current_led_state = 'off'
                self.left_lamp.set_state(False)
                self.right_lamp.set_state(False)
            elif new_state in ['W', 'F'] and self.current_button_state == 'pressed':
                self.current_led_state = 'on'
                self.left_lamp.set_state(True)
                self.right_lamp.set_state(True)
            
            # Log PWF state change
            cursor.execute("INSERT INTO signals_log (signal_name, value, source) VALUES (%s, %s, %s)",
                          ('pwf_state_change', new_state, 'GUI'))
            conn.commit()
            conn.close()
            
            self.log(f"PWF state changed to {new_state}")
            self.log(f"Sent buttonBB: {button_value} and LED: {led_value}")
            self.update_ui()
            
        except Exception as e:
            self.log(f"Error changing PWF state: {str(e)}")
            # Revert button state on error
            if self.current_pwf_state == 'P':
                self.p_btn.setChecked(True)
            elif self.current_pwf_state == 'S':
                self.s_btn.setChecked(True)
            elif self.current_pwf_state == 'W':
                self.w_btn.setChecked(True)
            elif self.current_pwf_state == 'F':
                self.f_btn.setChecked(True)

    def check_pwf_state(self):
        if self.offline_mode or not self.connection_successful:
            return
            
        try:
            conn = db.get_connection()
            if conn is None:
                raise Exception("Could not get connection")
                
            cursor = conn.cursor()
            cursor.execute("SELECT state FROM pwf_state ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            
            if result and result[0] != self.current_pwf_state:
                new_state = result[0]
                self.current_pwf_state = new_state
                if self.current_pwf_state == 'P':
                    self.p_btn.setChecked(True)
                elif self.current_pwf_state == 'S':
                    self.s_btn.setChecked(True)
                elif self.current_pwf_state == 'W':
                    self.w_btn.setChecked(True)
                elif self.current_pwf_state == 'F':
                    self.f_btn.setChecked(True)
                
                # Force LEDs off in P or S
                if new_state in ['P', 'S'] and self.current_led_state == 'on':
                    self.current_led_state = 'off'
                    self.current_button_state = 'not pressed'
                    if self.connection_successful:
                        cursor.execute("INSERT INTO signals_log (signal_name, value, source) VALUES (%s, %s, %s)",
                                      ('led', 'off', 'GUI'))
                        cursor.execute("INSERT INTO signals_log (signal_name, value, source) VALUES (%s, %s, %s)",
                                      ('button', 'not pressed', 'GUI'))
                        db.update_states('off', 'not pressed')
                        try:
                            network.send_udp_message("led1_toggle", '0')
                            self.log("LEDs turned off due to PWF state change to Park or StandBy, UDP sent")
                        except Exception as e:
                            self.log(f"LEDs turned off due to PWF state change, but UDP failed: {str(e)}")
                        conn.commit()
                    self.left_lamp.set_state(False)
                    self.right_lamp.set_state(False)
                self.log(f"PWF state updated to {self.current_pwf_state}")
                self.update_ui()
            conn.close()
        except Exception as e:
            self.log(f"Error checking PWF state: {str(e)}")

    def go_back(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            if project_root not in sys.path:
                sys.path.append(project_root)
            from components.WelcomeWindow import WelcomeWindow
            self.close()
            self.welcome_window = WelcomeWindow()
            self.welcome_window.show()
        except Exception as e:
            self.log(f"Error going back: {str(e)}")
            print(f"Error going back: {str(e)}")

    def log(self, message):
        now = datetime.now().strftime('%H:%M:%S')
        if hasattr(self, 'log_box'):
            self.log_box.append(f"[{now}] {message}")
        else:
            print(f"Log: {message}")

    def closeEvent(self, event):
        if hasattr(self, 'db_watcher') and self.db_watcher is not None:
            self.db_watcher.stop()
        if hasattr(self, 'pwf_timer') and self.pwf_timer.isActive():
            self.pwf_timer.stop()
        super().closeEvent(event)