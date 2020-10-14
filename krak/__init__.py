import atexit
from .connect import send
from .config import settings  # noqa
from . import tools, config, examples, units, spatial  # noqa
from .units import Unit  # noqa
from .mesh import load_mesh, load_points, load_lines  # noqa


atexit.register(send)
