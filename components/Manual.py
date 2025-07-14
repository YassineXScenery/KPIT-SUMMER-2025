import os
import sys
import socket
import json
import threading
import time
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QTextEdit,
    QVBoxLayout, QHBoxLayout, QFrame, QButtonGroup
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint, QObject
from PyQt5.QtGui import (
    QPainter, QBrush, QColor,
    QRadialGradient, QLinearGradient, QFont, QPixmap
)
import db
from .socket_manager import SocketManager

class CarLampWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 300)
        self.on = False
        self.glow_intensity = 0
        self.car_image = None
        self.car_pos = 0
        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self.update_glow)
        self.glow_timer.start(50)
        
    def load_car_image(self, path):
        if os.path.exists(path):
            self.car_image = QPixmap(path)
            self.car_image = self.car_image.scaled(600, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            print(f"Car image not found at: {path}")
        
    def set_state(self, on):
        self.on = on
        self.update()
        
    def move_left(self):
        self.car_pos = max(-100, self.car_pos - 20)
        self.update()
        
    def move_right(self):
        self.car_pos = min(100, self.car_pos + 20)
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
        
        if self.car_image:
            x_pos = self.car_pos + (self.width() - self.car_image.width()) // 2
            y_pos = (self.height() - self.car_image.height()) // 2
            painter.drawPixmap(x_pos, y_pos, self.car_image)
            
            if self.on or self.glow_intensity > 0:
                left_light_pos = QPoint(x_pos + int(self.car_image.width()*0.25), 
                                      y_pos + int(self.car_image.height()*0.5))
                right_light_pos = QPoint(x_pos + int(self.car_image.width()*0.75), 
                                       y_pos + int(self.car_image.height()*0.5))
                
                light_radius = int(self.width()*0.08)
                
                gradient = QRadialGradient(left_light_pos, light_radius*2)
                gradient.setColorAt(0, QColor(255, 230, 180, int(200 * self.glow_intensity / 100)))
                gradient.setColorAt(1, QColor(255, 200, 100, 0))
                painter.setBrush(QBrush(gradient))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(left_light_pos, light_radius*2, light_radius*2)
                
                gradient = QRadialGradient(right_light_pos, light_radius*2)
                gradient.setColorAt(0, QColor(255, 230, 180, int(200 * self.glow_intensity / 100)))
                gradient.setColorAt(1, QColor(255, 200, 100, 0))
                painter.setBrush(QBrush(gradient))
                painter.drawEllipse(right_light_pos, light_radius*2, light_radius*2)

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
        
        # Initialize states
        self.current_led_state = 'off'
        self.current_button_state = 'not pressed'
        self.current_pwf_state = None
        self.protocol = 'CAN'  # Default protocol
        self.last_db_change = None

        # Socket communication
        self.socket_manager = SocketManager()
        self.socket_manager.update_received.connect(self.handle_socket_update)
        self.socket_manager.peer_discovered.connect(self.handle_new_peer)
        self.socket_manager.start()

        # Setup UI
        self.init_ui()

        # Start connection monitoring
        self.log("Application started")
        self.attempt_connection()

        # Setup timers
        self.signals_watcher = QTimer(self)
        self.signals_watcher.timeout.connect(self.check_new_signals)
        self.signals_watcher.start(1000)

    def init_ui(self):
        self.setStyleSheet("""
            QWidget { 
                background-color: #1a1a2e; 
                color: #e6e6e6; 
            }
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

        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
        car_path = os.path.join(project_root, "assets", "car.png")
        
        self.car_lamp_widget = CarLampWidget()
        if os.path.exists(car_path):
            self.car_lamp_widget.load_car_image(car_path)
        else:
            print(f"Warning: Car image not found at {car_path}")
            
        self.toggle_btn = PhysicalButton("TOGGLE\nBUTTON")
        self.status_label = QLabel("LAMPS ARE OFF")
        self.status_label.setFont(QFont('Arial', 16))
        self.log_box = QTextEdit()
        self.log_box.setMinimumHeight(300)
        self.log_box.setFont(QFont('Arial', 14))
        self.log_box.setReadOnly(True)

        self.connection_status = QLabel("Peers: 0 | DB: Connecting...")
        self.connection_status.setFont(QFont('Arial', 12))

        self.move_left_btn = QPushButton("←")
        self.move_right_btn = QPushButton("→")
        self.move_left_btn.clicked.connect(self.car_lamp_widget.move_left)
        self.move_right_btn.clicked.connect(self.car_lamp_widget.move_right)
        
        arrow_btn_style = """
            QPushButton {
                font-size: 20pt;
                padding: 10px 20px;
                background-color: #404040;
                border: 2px solid #303030;
                border-radius: 5px;
                color: white;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
        """
        self.move_left_btn.setStyleSheet(arrow_btn_style)
        self.move_right_btn.setStyleSheet(arrow_btn_style)

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

        pwf_button_style = """
            QPushButton {
                background-color: #404040;
                border: 3px solid #151515;
                border-radius: 12px;
                color: white;
                font-size: 28pt;
                padding: 8px;
                min-width: 80px;
                min-height: 60px;
            }
            QPushButton:checked {
                background-color: #606060;
                border: 3px solid #00ff00;
                color: #00ff00;
                font-weight: bold;
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

        self.pwf_group = QButtonGroup(self)
        self.pwf_group.setExclusive(True)
        self.pwf_group.addButton(self.p_btn)
        self.pwf_group.addButton(self.s_btn)
        self.pwf_group.addButton(self.w_btn)
        self.pwf_group.addButton(self.f_btn)
        self.pwf_group.buttonClicked.connect(self.on_pwf_state_change)

        # Protocol selection buttons
        self.protocol_group = QButtonGroup(self)
        
        protocol_button_style = """
            QPushButton {
                background-color: #404040;
                border: 2px solid #151515;
                border-radius: 8px;
                color: white;
                padding: 15px 25px;
                font-size: 20pt;
                min-width: 120px;
                min-height: 70px;
            }
            QPushButton:checked {
                background-color: #606060;
                border: 3px solid #00ff00;
                color: #00ff00;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
        """

        self.can_btn = QPushButton('CAN')
        self.can_btn.setCheckable(True)
        self.can_btn.setChecked(True)
        self.can_btn.setStyleSheet(protocol_button_style)
        
        self.lin_btn = QPushButton('LIN')
        self.lin_btn.setCheckable(True)
        self.lin_btn.setStyleSheet(protocol_button_style)
        
        self.protocol_group.addButton(self.can_btn)
        self.protocol_group.addButton(self.lin_btn)
        self.protocol_group.buttonClicked.connect(self.on_protocol_change)

        top_bar = QHBoxLayout()
        pwf_label = QLabel("PWF State:")
        pwf_label.setFont(QFont('Arial', 16))
        top_bar.addWidget(pwf_label)
        top_bar.addWidget(self.p_btn)
        top_bar.addWidget(self.s_btn)
        top_bar.addWidget(self.w_btn)
        top_bar.addWidget(self.f_btn)
        top_bar.addSpacing(20)
        
        protocol_label = QLabel("Protocol:")
        protocol_label.setFont(QFont('Arial', 16))
        top_bar.addWidget(protocol_label)
        top_bar.addWidget(self.can_btn)
        top_bar.addWidget(self.lin_btn)
        top_bar.addSpacing(20)
        
        top_bar.addStretch()
        top_bar.addWidget(self.connection_status)
        top_bar.addWidget(self.back_btn)
        top_bar.setContentsMargins(10, 10, 10, 10)
        top_bar.setSpacing(15)

        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        control_layout.addWidget(self.toggle_btn)
        control_layout.addWidget(self.move_left_btn)
        control_layout.addWidget(self.car_lamp_widget)
        control_layout.addWidget(self.move_right_btn)
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

    def on_protocol_change(self, button):
        self.protocol = button.text()
        self.log(f"Protocol changed to {self.protocol}")

    def go_back(self):
        """Return to main window"""
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

    def handle_socket_update(self, message):
        if message.get('type') == 'state_update':
            if message.get('source') == f"GUI_{socket.gethostname()}":
                return
                
            self.blockSignals(True)
            
            protocol = message.get('protocol', 'CAN')
            self.can_btn.setChecked(protocol == 'CAN')
            self.lin_btn.setChecked(protocol == 'LIN')
            
            if 'pwf_state' in message:
                new_pwf_state = message['pwf_state']
                if new_pwf_state != self.current_pwf_state:
                    self.current_pwf_state = new_pwf_state
                    self._update_pwf_buttons()
                    self.log(f"PWF state updated via socket to {new_pwf_state} (via {protocol})")
                    
                    if new_pwf_state in ['P', 'S'] and self.current_led_state == 'on':
                        self.current_led_state = 'off'
                        self.car_lamp_widget.set_state(False)
            
            if 'led_state' in message:
                if self.current_pwf_state in ['W', 'F']:
                    new_led_state = message['led_state']
                    if new_led_state != self.current_led_state:
                        self.current_led_state = new_led_state
                        self.car_lamp_widget.set_state(new_led_state == 'on')
                        self.log(f"LED state updated via socket to {new_led_state} (via {protocol})")
                elif message['led_state'] == 'on':
                    self.current_led_state = 'off'
                    self.car_lamp_widget.set_state(False)
            
            if 'button_state' in message:
                new_button_state = message['button_state']
                if new_button_state != self.current_button_state:
                    self.current_button_state = new_button_state
                    self.log(f"Button state updated via socket to {new_button_state} (via {protocol})")
                    
                    if self.current_pwf_state in ['W', 'F']:
                        new_led = 'on' if new_button_state == 'pressed' else 'off'
                        if new_led != self.current_led_state:
                            self.current_led_state = new_led
                            self.car_lamp_widget.set_state(new_led == 'on')
            
            self.update_ui()
            self.blockSignals(False)

    def handle_new_peer(self, peer_ip):
        self.log(f"Discovered new peer: {peer_ip}")
        self.connection_status.setText(f"Peers: {len(self.socket_manager.peers)} | DB: Online")

    def broadcast_state(self):
        message = {
            'type': 'state_update',
            'led_state': self.current_led_state,
            'button_state': self.current_button_state,
            'pwf_state': self.current_pwf_state,
            'protocol': self.protocol,
            'source': f"GUI_{socket.gethostname()}",
            'timestamp': datetime.now().isoformat()
        }
        self.socket_manager.send_update(message)

    def attempt_connection(self):
        try:
            conn = db.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchall()
                conn.close()
                
                if not self.signals_watcher.isActive():
                    self.signals_watcher.start(1000)
                
                self.p_btn.setEnabled(True)
                self.s_btn.setEnabled(True)
                self.w_btn.setEnabled(True)
                self.f_btn.setEnabled(True)
                
                self.connection_status.setText(f"Peers: {len(self.socket_manager.peers)} | DB: Online")
                self.load_initial_state()
            else:
                self.connection_status.setText(f"Peers: {len(self.socket_manager.peers)} | DB: Offline")
        except Exception as e:
            self.connection_status.setText(f"Peers: {len(self.socket_manager.peers)} | DB: Offline")
        
        QTimer.singleShot(5000, self.attempt_connection)

    def check_new_signals(self):
        conn = None
        try:
            conn = db.get_connection()
            if conn is None:
                self.connection_status.setText(f"Peers: {len(self.socket_manager.peers)} | DB: Offline")
                return
                
            cursor = conn.cursor()
            
            cursor.execute("SELECT state FROM pwf_state WHERE is_active = 1 ORDER BY timestamp DESC LIMIT 1")
            pwf_result = cursor.fetchone()
            if pwf_result:
                new_pwf_state = pwf_result[0]
                if new_pwf_state != self.current_pwf_state:
                    self.current_pwf_state = new_pwf_state
                    self._update_pwf_buttons()
                    self.log(f"PWF state updated from DB to {new_pwf_state}")
                    
                    if new_pwf_state in ['P', 'S'] and self.current_led_state == 'on':
                        self.current_led_state = 'off'
                        self.car_lamp_widget.set_state(False)
                        self._update_led_in_db('off')
            
            cursor.execute("SELECT value, protocol FROM signals_log WHERE signal_name = 'led' ORDER BY id DESC LIMIT 1")
            led_result = cursor.fetchone()
            if led_result:
                new_led_state, protocol = led_result
                if self.current_pwf_state in ['W', 'F']:
                    if new_led_state != self.current_led_state:
                        self.current_led_state = new_led_state
                        self.car_lamp_widget.set_state(new_led_state == 'on')
                        self.log(f"LED state updated from DB to {new_led_state} (via {protocol})")
                elif new_led_state == 'on':
                    self.current_led_state = 'off'
                    self.car_lamp_widget.set_state(False)
                    self._update_led_in_db('off')
            
            cursor.execute("SELECT value, protocol FROM signals_log WHERE signal_name = 'button' ORDER BY id DESC LIMIT 1")
            button_result = cursor.fetchone()
            if button_result:
                new_button_state, protocol = button_result
                if new_button_state != self.current_button_state:
                    self.current_button_state = new_button_state
                    self.log(f"Button state updated from DB to {new_button_state} (via {protocol})")
                    
                    if self.current_pwf_state in ['W', 'F']:
                        new_led = 'on' if new_button_state == 'pressed' else 'off'
                        if new_led != self.current_led_state:
                            self.current_led_state = new_led
                            self.car_lamp_widget.set_state(new_led == 'on')
                            self._update_led_in_db(new_led)
            
            self.update_ui()
            
        except Exception as e:
            self.log(f"Error checking signals: {str(e)}")
            self.connection_status.setText(f"Peers: {len(self.socket_manager.peers)} | DB: Offline")
        finally:
            if conn and conn.is_connected():
                conn.close()

    def _update_led_in_db(self, state):
        conn = None
        try:
            conn = db.get_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO signals_log (signal_name, value, source, timestamp, protocol)
                VALUES (%s, %s, %s, %s, %s)
            """, ('led', state, 'GUI', datetime.now().isoformat(), self.protocol))
            conn.commit()
            self.broadcast_state()
        except Exception as e:
            self.log(f"Error updating LED in DB: {str(e)}")
        finally:
            if conn and conn.is_connected():
                conn.close()

    def toggle_button(self):
        if self.current_pwf_state in ['P', 'S']:
            self.log("Button disabled in P/S modes")
            return
            
        new_button_state = 'pressed' if self.current_button_state == 'not pressed' else 'not pressed'
        new_led_state = 'on' if new_button_state == 'pressed' else 'off'
        
        conn = None
        try:
            conn = db.get_connection()
            if conn is None:
                raise Exception("Could not get database connection")
            
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO signals_log (signal_name, value, source, timestamp, protocol)
                VALUES (%s, %s, %s, %s, %s)
            """, ('button', new_button_state, 'GUI', datetime.now().isoformat(), self.protocol))
            
            cursor.execute("""
                INSERT INTO signals_log (signal_name, value, source, timestamp, protocol)
                VALUES (%s, %s, %s, %s, %s)
            """, ('led', new_led_state, 'GUI', datetime.now().isoformat(), self.protocol))
            
            conn.commit()
            
            self.current_button_state = new_button_state
            self.current_led_state = new_led_state
            self.car_lamp_widget.set_state(new_led_state == 'on')
            self.broadcast_state()
            self.log(f"Button toggled to {new_button_state}, LED to {new_led_state} (via {self.protocol})")
            
            self.update_ui()
        except Exception as e:
            self.log(f"Error toggling button: {str(e)}")
        finally:
            if conn and conn.is_connected():
                conn.close()

    def on_pwf_state_change(self, button):
        new_state = button.text()
        current_state = self.current_pwf_state
        
        invalid_transitions = [
            ('P', 'F'), ('P', 'W'),
            ('F', 'P'), ('W', 'P')
        ]
        
        if current_state and (current_state, new_state) in invalid_transitions:
            self.log(f"Invalid PWF transition from {current_state} to {new_state}")
            self.blockSignals(True)
            for btn in self.pwf_group.buttons():
                btn.setChecked(btn.text() == current_state)
            self.blockSignals(False)
            return
            
        conn = None
        try:
            conn = db.get_connection()
            if conn is None:
                raise Exception("Could not get database connection")
            
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE pwf_state 
                SET is_active = 0
            """)
            
            cursor.execute("""
                UPDATE pwf_state 
                SET is_active = 1, timestamp = CURRENT_TIMESTAMP
                WHERE state = %s
            """, (new_state,))
            
            cursor.execute("""
                INSERT INTO signals_log (signal_name, value, source, timestamp, protocol)
                VALUES (%s, %s, %s, %s, %s)
            """, ('pwf_state_change', new_state, 'GUI', datetime.now().isoformat(), self.protocol))
            
            conn.commit()
            
            self.current_pwf_state = new_state
            
            if new_state in ['P', 'S'] and self.current_led_state == 'on':
                self.current_led_state = 'off'
                self.car_lamp_widget.set_state(False)
                self._update_led_in_db('off')
            
            self.broadcast_state()
            self.log(f"PWF state changed to {new_state} (via {self.protocol})")
            self.update_ui()
        except Exception as e:
            self.log(f"Error changing PWF state: {str(e)}")
            self.blockSignals(True)
            for btn in self.pwf_group.buttons():
                btn.setChecked(btn.text() == current_state)
            self.blockSignals(False)
        finally:
            if conn and conn.is_connected():
                conn.close()

    def load_initial_state(self):
        conn = None
        try:
            conn = db.get_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT state FROM pwf_state 
                WHERE is_active = 1
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            pwf_state = cursor.fetchone()
            if pwf_state:
                self.current_pwf_state = pwf_state[0]
                self._update_pwf_buttons()
                self.log(f"Initial PWF state loaded: {self.current_pwf_state}")
            else:
                self.log("No active PWF state found in database")
            
            cursor.execute("SELECT value, protocol FROM signals_log WHERE signal_name = 'led' ORDER BY id DESC LIMIT 1")
            led_state = cursor.fetchone()
            if led_state:
                self.current_led_state = led_state[0]
                self.car_lamp_widget.set_state(self.current_led_state == 'on')
                self.log(f"Initial LED state loaded: {self.current_led_state} (via {led_state[1]})")
            
            cursor.execute("SELECT value, protocol FROM signals_log WHERE signal_name = 'button' ORDER BY id DESC LIMIT 1")
            button_state = cursor.fetchone()
            if button_state:
                self.current_button_state = button_state[0]
                self.log(f"Initial button state loaded: {self.current_button_state} (via {button_state[1]})")
            
            self.update_ui()
            self.broadcast_state()
        except Exception as e:
            self.log(f"Error loading initial state: {str(e)}")
        finally:
            if conn and conn.is_connected():
                conn.close()

    def _update_pwf_buttons(self):
        self.blockSignals(True)
        for button in self.pwf_group.buttons():
            button.setChecked(button.text() == self.current_pwf_state)
            button.setEnabled(True)
        self.blockSignals(False)

    def update_ui(self):
        if self.current_pwf_state:
            status_text = f"LAMPS ARE {self.current_led_state.upper()} (PWF: {self.current_pwf_state}, Protocol: {self.protocol})"
        else:
            status_text = "LAMPS ARE OFF (No PWF state selected)"
        self.status_label.setText(status_text)
        
        self.toggle_btn.setText(f"TOGGLE\nBUTTON ({self.current_button_state.replace('_', ' ').title()})")
        self.toggle_btn.setEnabled(self.current_pwf_state in ['W', 'F'])

    def log(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_box.append(f"[{timestamp}] {message}")
        self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

    def closeEvent(self, event):
        if hasattr(self, 'signals_watcher') and self.signals_watcher.isActive():
            self.signals_watcher.stop()
        if hasattr(self, 'socket_manager'):
            self.socket_manager.stop()
            
        time.sleep(0.5)
        super().closeEvent(event)

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ManualWindow()
    window.show()
    sys.exit(app.exec_())