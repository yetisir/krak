import atexit

from . import tools, examples, config  # noqa
from .mesh import load_mesh, load_points, load_lines  # noqa
from .connect import send

settings = config.Settings()

atexit.register(send)
