from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QFont
from datetime import datetime
import db

class ControlButton(QPushButton):
    def __init__(self, protocol, parent=None):
        super().__init__(f"TOGGLE\nBUTTON {protocol}", parent)
        self.protocol = protocol
        self.parent_window = parent
        self.current_led_state = 'off'
        self.current_button_state = 'not pressed'
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
        self.clicked.connect(self.toggle_button)

    def toggle_button(self):
        conn = None
        try:
            conn = db.get_connection()
            if conn is None:
                raise Exception("Could not get database connection")
            
            # Check PWF state and prevent LED activation in P/S modes
            if hasattr(self.parent_window, 'current_pwf_state'):
                if self.parent_window.current_pwf_state in ['P', 'S']:
                    self.parent_window.log(f"Cannot toggle LED in {self.parent_window.current_pwf_state} mode")
                    return
            
            cursor = conn.cursor()
            
            if hasattr(self.parent_window, 'protocol'):
                self.parent_window.protocol = self.protocol
                if hasattr(self.parent_window, 'can_btn') and hasattr(self.parent_window, 'lin_btn'):
                    self.parent_window.can_btn.setChecked(self.protocol == 'CAN')
                    self.parent_window.lin_btn.setChecked(self.protocol == 'LIN')
            
            new_button_state = 'pressed' if self.current_button_state == 'not pressed' else 'not pressed'
            
            # Only allow LED activation in W/F modes
            if hasattr(self.parent_window, 'current_pwf_state'):
                new_led_state = 'on' if (new_button_state == 'pressed' and 
                                       self.parent_window.current_pwf_state in ['W', 'F']) else 'off'
            else:
                new_led_state = 'off'
            
            if self.protocol == 'CAN':
                cursor.execute("""
                    INSERT INTO signals_log (signal_name, value, source, timestamp, protocol)
                    VALUES (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s)
                """, 
                ('button', new_button_state, 'GUI', datetime.now().isoformat(), self.protocol,
                 'led', new_led_state, 'GUI', datetime.now().isoformat(), self.protocol))
            else:  # LIN
                cursor.execute("""
                    INSERT INTO signals_log (signal_name, value, source, timestamp, protocol)
                    VALUES (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s)
                """, 
                ('buttonL', new_button_state, 'GUI', datetime.now().isoformat(), self.protocol,
                 'ledL', new_led_state, 'GUI', datetime.now().isoformat(), self.protocol))
            
            conn.commit()
            
            self.current_button_state = new_button_state
            self.current_led_state = new_led_state
            
            if hasattr(self.parent_window, 'broadcast_state'):
                self.parent_window.broadcast_state()
            
            if hasattr(self.parent_window, 'log'):
                self.parent_window.log(f"Button toggled to {new_button_state}, LED to {new_led_state} (via {self.protocol})")
            
            if hasattr(self.parent_window, 'car_lamp_widget'):
                self.parent_window.car_lamp_widget.set_state(new_led_state == 'on')
            
        except Exception as e:
            if hasattr(self.parent_window, 'log'):
                self.parent_window.log(f"Error toggling button: {str(e)}")
            else:
                print(f"Error toggling button: {str(e)}")
        finally:
            if conn and conn.is_connected():
                conn.close()