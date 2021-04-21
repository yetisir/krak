import pyvista
import pyvistaqt


from . import utils


class Window(metaclass=utils.Singleton):
    def __init__(self):
        self.ipython = utils.ipython()

        if self.ipython:
            self._plotter = pyvista.Plotter()
            self.ipython = True
        else:
            self._plotter = pyvistaqt.BackgroundPlotter()

    @property
    def plotter(self):
        if self.ipython:
            if self._plotter is None:
                self._plotter = pyvista.Plotter()
        else:
            if not self._plotter.isVisible():
                self._plotter = pyvistaqt.BackgroundPlotter()

        return self._plotter

    def add_mesh(self, mesh, show=False, **kwargs):
        plotter = self.plotter
        plotter.add_mesh(mesh, **kwargs)
        if self.ipython and show:
            plotter.show()
            self._plotter = None
