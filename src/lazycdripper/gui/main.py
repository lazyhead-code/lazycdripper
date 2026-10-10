"""Desktop GUI application entry point for Lazy CD Ripper."""

import sys
from lazycdripper.gui.main_window import MainWindow

try:
    from PySide6.QtWidgets import QApplication
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


def main():
    if not HAVE_QT:
        print("PySide6 is not installed. Please run: pip install 'pyside6>=6.6.0'")
        return 1

    # On Windows, set explicit AppUserModelID so taskbar groups properly and shows app icon
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("lazyhead.lazycdripper.app.1")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("Lazy CD Ripper")
    app.setOrganizationName("Lazyhead Code")

    from lazycdripper.gui.main_window import locate_app_icon_path
    icon_path = locate_app_icon_path()
    if icon_path:
        from PySide6.QtGui import QIcon
        app.setWindowIcon(QIcon(str(icon_path)))

    from lazycdripper.gui.theme import DARK_ROCK_STYLESHEET
    app.setStyleSheet(DARK_ROCK_STYLESHEET)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
