from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QRadialGradient, QPixmap, QBrush
import os
import db   

class LampControl(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(1200, 300)  # Double width to accommodate both cars
        self.on = False
        self.glow_intensity = 0
        self.car_image = None
        self.car_back_image = None
        self.car_pos = 0
        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self.update_glow)
        self.glow_timer.start(30)  # Faster update for smoother glow
    
    def load_car_image(self, path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
        
        # Load front car image
        car_path = os.path.join(project_root, "assets", "car.png")
        if os.path.exists(car_path):
            self.car_image = QPixmap(car_path)
            self.car_image = self.car_image.scaled(600, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            print(f"Front car image not found at: {car_path}")
        
        # Load back car image
        car_back_path = os.path.join(project_root, "assets", "carback.png")
        if os.path.exists(car_back_path):
            self.car_back_image = QPixmap(car_back_path)
            self.car_back_image = self.car_back_image.scaled(600, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            print(f"Back car image not found at: {car_back_path}")
    
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
            self.glow_intensity += 10  # Faster intensity increase
        elif not self.on and self.glow_intensity > 0:
            self.glow_intensity -= 5
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.car_image and self.car_back_image:
            # Calculate positions for both cars
            x_pos_front = self.car_pos + (self.width()//2 - self.car_image.width()) // 2
            x_pos_back = self.car_pos + (self.width()//2 - self.car_back_image.width()) // 2 + self.width()//2
            y_pos = (self.height() - self.car_image.height()) // 2
            
            # Draw front car (left side)
            painter.drawPixmap(x_pos_front, y_pos, self.car_image)
            
            # Draw back car (right side)
            painter.drawPixmap(x_pos_back, y_pos, self.car_back_image)
            
            if self.on or self.glow_intensity > 0:
                light_radius = int(self.width()*0.04)  # Increased radius for bigger lights
                glow_radius = light_radius * 3  # Larger glow area
                
                # Front car lights (white/yellow) - two lights at front corners
                front_left_light = QPoint(
                    x_pos_front + int(self.car_image.width()*0.15), 
                    y_pos + int(self.car_image.height()*0.455))
                front_right_light = QPoint(
                    x_pos_front + int(self.car_image.width()*0.85), 
                    y_pos + int(self.car_image.height()*0.455)
                )
                
                # Draw front left light (brighter white-yellow)
                gradient = QRadialGradient(front_left_light, glow_radius)
                gradient.setColorAt(0, QColor(255, 255, 220, int(255 * self.glow_intensity / 100)))  # Brighter center
                gradient.setColorAt(0.3, QColor(255, 240, 180, int(220 * self.glow_intensity / 100)))
                gradient.setColorAt(1, QColor(255, 200, 100, 0))
                painter.setBrush(QBrush(gradient))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(front_left_light, glow_radius, glow_radius)
                
                # Draw front right light
                gradient = QRadialGradient(front_right_light, glow_radius)
                gradient.setColorAt(0, QColor(255, 255, 220, int(255 * self.glow_intensity / 100)))  # Brighter center
                gradient.setColorAt(0.3, QColor(255, 240, 180, int(220 * self.glow_intensity / 100)))
                gradient.setColorAt(1, QColor(255, 200, 100, 0))
                painter.setBrush(QBrush(gradient))
                painter.drawEllipse(front_right_light, glow_radius, glow_radius)
                
                # Back car lights (red) - two lights at rear corners
                back_left_light = QPoint(
                    x_pos_back + int(self.car_back_image.width()*0.15), 
                    y_pos + int(self.car_back_image.height()*0.43)
                )
                back_right_light = QPoint(
                    x_pos_back + int(self.car_back_image.width()*0.85), 
                    y_pos + int(self.car_back_image.height()*0.43)
                )
                
                # Draw back left light (brighter red)
                gradient = QRadialGradient(back_left_light, glow_radius)
                gradient.setColorAt(0, QColor(255, 150, 150, int(255 * self.glow_intensity / 100)))  # Brighter center
                gradient.setColorAt(0.3, QColor(255, 100, 100, int(220 * self.glow_intensity / 100)))
                gradient.setColorAt(1, QColor(255, 50, 50, 0))
                painter.setBrush(QBrush(gradient))
                painter.drawEllipse(back_left_light, glow_radius, glow_radius)
                
                # Draw back right light (red)
                gradient = QRadialGradient(back_right_light, glow_radius)
                gradient.setColorAt(0, QColor(255, 150, 150, int(255 * self.glow_intensity / 100)))  # Brighter center
                gradient.setColorAt(0.3, QColor(255, 100, 100, int(220 * self.glow_intensity / 100)))
                gradient.setColorAt(1, QColor(255, 50, 50, 0))
                painter.setBrush(QBrush(gradient))
                painter.drawEllipse(back_right_light, glow_radius, glow_radius)