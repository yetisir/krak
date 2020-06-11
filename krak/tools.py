from collections import Counter

import pyvista

from . import mesh


def load_mesh(file_name, file_type=None, dimension=None):
    pv_mesh = pyvista.read_meshio(file_name, file_type)
    if dimension is None:
        dimension = _guess_mesh_dimension(pv_mesh)

    return mesh.dimension_class(dimension)(pv_mesh)

def _guess_mesh_dimension(pv_mesh):
    cell_dimensions = [
        mesh.cell_dimension(cell_type) for cell_type in pv_mesh.celltypes]
    dimension_count = Counter(cell_dimensions)
    return max(dimension_count, key=dimension_count.get)
