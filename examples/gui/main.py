import sys

from PyQt5 import QtWidgets
from . import window


def main():
    app = QtWidgets.QApplication(sys.argv)
    window.Window(app=app)
