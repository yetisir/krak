import pyvistaqt

from . import utils


class Window(metaclass=utils.Singleton):
    def __init__(self):
        self._plotter = pyvistaqt.BackgroundPlotter()

    @property
    def plotter(self):
        if not self._plotter.isVisible():
            self._plotter = pyvistaqt.BackgroundPlotter()

        return self._plotter
