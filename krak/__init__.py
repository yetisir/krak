from .connect import send
import atexit
import pint

units = pint.UnitRegistry()

from . import tools, examples, config  # noqa
from .mesh import load_mesh, load_points, load_lines  # noqa

settings = config.Settings()

atexit.register(send)
