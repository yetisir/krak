from collections import Counter

import pyvista

from . import common


def load_mesh(file_name, file_type=None, dimension=None):
    mesh = pyvista.read_meshio(file_name, file_type)
    if dimension is None:
        dimension = _guess_mesh_dimension(mesh)

    return common.dimension_mesh_map[dimension](mesh)


def _guess_mesh_dimension(mesh):
    cell_dimensions = [
        common.cell_dimension_map[cell_type] for cell_type in mesh.celltypes]
    dimension_count = Counter(cell_dimensions)
    return max(dimension_count, key=dimension_count.get)
