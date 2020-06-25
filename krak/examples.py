from pyvista import examples

from . import mesh


def random_hills():
    return mesh.load_mesh(examples.load_random_hills())
