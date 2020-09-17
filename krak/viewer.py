import pyvistaqt

from . import utils


class Window(metaclass=utils.Singleton):
    def __init__(self):
        self.plotter = pyvistaqt.BackgroundPlotter()
