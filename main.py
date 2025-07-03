import sys
import os
from PyQt5.QtWidgets import QApplication
from components.WelcomeWindow import WelcomeWindow

if __name__ == "__main__":
    os.environ['QT_MULTIMEDIA_PREFERRED_PLUGINS'] = 'windowsmediafoundation'
    app = QApplication(sys.argv)
    window = WelcomeWindow()
    window.show()
    sys.exit(app.exec_())