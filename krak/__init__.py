import atexit

from . import tools, examples, config, units, spatial  # noqa
from .connect import send
from .units import parse as unit  # noqa
from .mesh import load_mesh, load_points, load_lines  # noqa

settings = config.Settings()

atexit.register(send)
