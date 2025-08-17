from PyQt5.QtWidgets import QApplication
from core.core_controller import CoreController
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = CoreController()
    controller.start()
    sys.exit(app.exec_())
