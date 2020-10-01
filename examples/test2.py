from PyQt5 import QtWidgets
# from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
# import os
# from pyqtconsole.console import PythonConsole


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)

        hour = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        temperature = [30, 32, 34, 32, 33, 31, 29, 32, 35, 45]

        # plot data: x, y values
        self.graphWidget.plot(hour, temperature)


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()


# #! /usr/bin/env python
# # -*- coding: utf-8 -*-

# import sys

# from qtpy.QtWidgets import QApplication
# from pyqtconsole.console import PythonConsole


# def greet():
#     print("hello world")


# if __name__ == '__main__':
#     app = QApplication([])

#     console = PythonConsole()
#     console.push_local_ns('greet', greet)
#     console.show()
#     console.eval_in_thread()
#     sys.exit(app.exec_())
