from collections import Counter

import pyvista
import meshio
import vtk

from . import mesh


def extrude_topography(surface, bottom_elevation):
    #TODO: rewrite to be coordinate system agnostic
    extruded_surface = surface.extrude(
        [0, 0, -1], surface.bounds[-1] - bottom_elevation)
    clipped_surface = extruded_surface.clip_closed(origin=[0, 0, bottom_elevation], normal=[0, 0, 1])
    #clipped_surface = surface._cleaned_surface().clip([0, 0, 1], [0, 0, bottom_elevation])
    return clipped_surface

def load_mesh(mesh, dimension=None, **kwargs):
    if isinstance(mesh, str):
        pv_mesh = pyvista.read_meshio(mesh, **kwargs)
    elif isinstance(mesh, pyvista.Common):
        pv_mesh = mesh
    elif isinstance(mesh, meshio.Mesh):
        pv_mesh = pyvista.from_meshio(mesh)
    elif isinstance(mesh, vtk.vtkDataSet):
        pv_mesh = pyvista.wrap(mesh)
    elif isinstance(mesh, mesh.Mesh):
        pv_mesh = mesh.pv_mesh

    return _mesh_from_pyvista(pv_mesh, dimension=dimension)


def _mesh_from_pyvista(pv_mesh, dimension=None):
    pv_mesh = pv_mesh.cast_to_unstructured_grid()
    if dimension is None:
        dimension = _guess_mesh_dimension(pv_mesh)

    return mesh.dimension_class(dimension)(pv_mesh)


def _guess_mesh_dimension(pv_mesh):
    cell_dimensions = [
        mesh.cell_dimension(cell_type) for cell_type in pv_mesh.celltypes]
    dimension_count = Counter(cell_dimensions)
    return max(dimension_count, key=dimension_count.get)
