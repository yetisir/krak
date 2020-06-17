from collections import Counter

import pymesh
import pyvista
import numpy as np
import meshio
import vtk

from . import mesh


def extrude_topography(surface, bottom_elevation):
    # TODO: rewrite to be coordinate system agnostic
    extruded_surface = surface.extrude(
        [0, 0, -1], surface.bounds[-1] - bottom_elevation)
    clipped_surface = extruded_surface.remesh().clip_closed(
        origin=[0, 0, bottom_elevation], normal=[0, 0, 1])
    return clipped_surface.remesh()


def create_mesh(points, cells, celltypes=None):
    # TODO: more efficient
    # TODO: add support for unstructured grids and points
    return load_mesh(pymesh.form_mesh(points, cells))


def load_mesh(unknown_mesh, dimension=None, **kwargs):
    if isinstance(unknown_mesh, str):
        pv_mesh = pyvista.read_meshio(unknown_mesh, **kwargs)
    elif isinstance(unknown_mesh, pyvista.Common):
        pv_mesh = unknown_mesh
    elif isinstance(unknown_mesh, meshio.Mesh):
        pv_mesh = pyvista.from_meshio(unknown_mesh)
    elif isinstance(unknown_mesh, vtk.vtkDataSet):
        pv_mesh = pyvista.wrap(unknown_mesh)
    elif isinstance(unknown_mesh, mesh.Mesh):
        pv_mesh = unknown_mesh.pv_mesh
    elif isinstance(unknown_mesh, pymesh.Mesh):
        pv_mesh = _pymesh_to_pyvista(unknown_mesh)
    elif isinstance(unknown_mesh, dict):
        pass
        # pv_mesh = _pymesh_to_pyvista(unknown_mesh)

    return _mesh_from_pyvista(pv_mesh, dimension=dimension)


def _pymesh_to_pyvista(pymesh_mesh):
    # TODO: handle line and volume cells
    cell_array = []
    for cell in pymesh_mesh.faces:
        cell_array.append(len(cell))
        cell_array.extend(cell)
    return pyvista.PolyData(pymesh_mesh.vertices, np.array(cell_array))


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
