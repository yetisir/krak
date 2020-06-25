# from .mesh import PointMesh, LineMesh, SurfaceMesh, VolumeMesh  # noqa
import atexit

from . import tools, examples
from .mesh import load_mesh  # noqa
from .connect import send


atexit.register(send)
