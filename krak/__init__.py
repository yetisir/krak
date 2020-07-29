import atexit

from . import tools, examples  # noqa
from .mesh import load_mesh  # noqa
from .connect import send


atexit.register(send)
