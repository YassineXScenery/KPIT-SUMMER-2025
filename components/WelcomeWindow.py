import os
import sys
import subprocess
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QApplication)
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from components.Manual import ManualWindow

class WelcomeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Car Component Test System")
        self.setFixedSize(800, 600)

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        # Video background setup
        self.video_widget = QVideoWidget(self)
        self.video_widget.setGeometry(0, 0, self.width(), self.height())
        self.video_widget.setStyleSheet("background: transparent; border: none;")
        self.video_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.media_player = QMediaPlayer(self)
        self.media_player.setVideoOutput(self.video_widget)
        
        video_path = os.path.abspath("assets/background.mp4")
        if os.path.exists(video_path):
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))
            self.media_player.setVolume(0)
            self.media_player.play()
        else:
            print(f"Background video not found at {video_path}")

        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        self.loop_timer = QTimer(self)
        self.loop_timer.timeout.connect(self.check_video_position)
        self.loop_timer.start(100)
        self.video_widget.lower()

        # Logo
        self.logo = QLabel(self)
        pixmap = QPixmap("assets/logo.png")
        if not pixmap.isNull():
            pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo.setPixmap(pixmap)
        self.logo.setStyleSheet("background: transparent; border: none;")
        self.logo.setAlignment(Qt.AlignCenter)

        # Title
        self.title = QLabel("Select Test Mode", self)
        self.title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: white;
            background: transparent;
            border: none;
        """)
        self.title.setAlignment(Qt.AlignCenter)

        # Buttons
        button_style = """
            QPushButton {
                background-color: rgba(0, 0, 0, 0.8);
                border: 2px solid #00aa00;
                border-radius: 10px;
                color: #00ff00;
                font-size: 16px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(0, 10, 0, 0.9);
                border: 3px solid #00ff00;
                color: #ffffff;
                padding: 7px;
            }
            QPushButton:pressed {
                background-color: rgba(0, 30, 0, 0.9);
                border: 2px solid #00ff00;
                color: #00ff00;
                padding: 8px;
            }
        """

        manual_btn = QPushButton("Manual Test", self)
        manual_btn.setFixedSize(200, 50)
        manual_btn.setStyleSheet(button_style)
        manual_btn.clicked.connect(self.open_manual)

        auto_btn = QPushButton("Automatic Test", self)
        auto_btn.setFixedSize(200, 50)
        auto_btn.setStyleSheet(button_style)
        auto_btn.clicked.connect(self.open_automatic)

        # Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.setSpacing(20)
        self.main_layout.addWidget(self.logo)
        self.main_layout.addWidget(self.title)
        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(manual_btn)
        self.main_layout.addWidget(auto_btn)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.resizeEvent = self.on_resize

    def on_resize(self, event):
        self.video_widget.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def handle_media_status(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.media_player.setPosition(0)
            self.media_player.play()

    def check_video_position(self):
        if self.media_player.position() >= self.media_player.duration() - 100:
            self.media_player.setPosition(0)

    def open_manual(self):
        self.media_player.stop()
        self.manual_window = ManualWindow()
        self.manual_window.show()
        self.close()

    def open_automatic(self):
        """Open test.robot in VS Code or create valid template if missing"""
        robot_file = os.path.abspath("test.robot")
        
        # Create valid template ONLY if file doesn't exist
        if not os.path.exists(robot_file):
            with open(robot_file, "w", encoding="utf-8") as f:
                f.write("*** Settings ***\n")
                f.write("Library    DatabaseLibrary\n")
                f.write("Library    OperatingSystem\n\n")
                f.write("*** Test Cases ***\n")
                f.write("Example Test Case\n")
                f.write("    [Documentation]    Sample test case\n")
                f.write("    Log    This is a valid test case\n")
                f.write("    # Add your test steps here\n\n")
                f.write("*** Keywords ***\n")
                f.write("# Add your custom keywords here\n")
        
        # Force VS Code to open the specific file
        try:
            if sys.platform == "win32":
                subprocess.run(f'code "{robot_file}"', shell=True, check=True)
            else:
                subprocess.run(["code", robot_file], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to open VS Code: {e}")
            # Fallback - open containing folder
            folder = os.path.dirname(robot_file)
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])

    def closeEvent(self, event):
        self.media_player.stop()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication([])
    window = WelcomeWindow()
    window.show()
    app.exec_()