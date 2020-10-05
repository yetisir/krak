import atexit

from . import tools, examples  # noqa
from .mesh import load_mesh, load_points, load_lines  # noqa
from .connect import send


atexit.register(send)
