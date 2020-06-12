from collections import Counter

import pyvista
import meshio

from . import mesh


def extrude_topography(surface, bottom_elevation):
    #TODO: rewrite to be coordinate system agnostic
    surface = surface.pv_mesh.extract_surface().clean()
    grid = pyvista.create_grid(surface)
    return grid.clip_surface(surface)


def load_mesh(mesh, dimension=None, **kwargs):
    if isinstance(mesh, str):
        pv_mesh = pyvista.read_meshio(mesh, **kwargs)
    elif isinstance(mesh, pyvista.Common):
        pv_mesh = mesh.cast_to_unstructured_grid()
    elif isinstance(mesh, meshio.Mesh):
        pv_mesh = pyvista.from_meshio(meshio_mesh)
    elif isinstance(mesh, vtk.vtkDataSet):
        pass
    elif isinstance(mesh, mesh.Mesh):
        pv_mesh = mesh.pv_mesh

    return _mesh_from_pyvista(pv_mesh, dimension=dimension)


def _mesh_from_pyvista(pv_mesh, dimension=None):
    if dimension is None:
        dimension = _guess_mesh_dimension(pv_mesh)

    return mesh.dimension_class(dimension)(pv_mesh)


def _guess_mesh_dimension(pv_mesh):
    cell_dimensions = [
        mesh.cell_dimension(cell_type) for cell_type in pv_mesh.celltypes]
    dimension_count = Counter(cell_dimensions)
    return max(dimension_count, key=dimension_count.get)
