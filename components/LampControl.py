from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QRadialGradient, QPixmap, QBrush
import os
import db   
class LampControl(QLabel):
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