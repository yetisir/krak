from collections import Counter
from abc import ABC, abstractmethod
import traceback

import meshio
import numpy as np
import pandas
import pymesh
import pyvista
import tetgen
import vtk


from . import spatial, remesh, utils


class Mesh(ABC):

    _registry = []

    def __init__(self, mesh, parents=None, register=True):
        super().__init__()

        self.pv_mesh = mesh.cast_to_unstructured_grid()
        if parents is None:
            self._parents = []
        else:
            self._parent = parents
        self._remove_invalid_cells()

        if register:
            self._registry.append(self)

    def __add__(self, other):
        return self.merge(other)

    def __sub__(self, other):
        pass

    @classmethod
    def from_file(cls, file_name, file_type=None):
        return cls(pyvista.read_meshio(file_name, file_type))

    @classmethod
    def from_pyvista(cls, mesh):
        return cls(mesh)

    @classmethod
    def from_vtk(cls, mesh):
        return cls(pyvista.wrap(mesh))  # untested

    @classmethod
    def from_meshio(cls, mesh):
        return cls(pyvista.from_meshio(mesh))

    def serialize(self):
        # TODO: serialize more efficiently

        return {
            'dimension': self.dimension,
            'points': self.points.values.tolist(),
            'point_arrays': {
                key: value.tolist() for key, value
                in self.pv_mesh.point_arrays.items()},
            'cells': self.pv_mesh.cells.tolist(),
            'celltypes': self.pv_mesh.celltypes.tolist(),
            'offset': self.pv_mesh.offset.tolist(),
            'cell_arrays': {
                key: value.tolist() for key, value
                in self.pv_mesh.cell_arrays.items()},
        }

    @property
    @abstractmethod
    def dimension(self):
        raise NotImplementedError

    def plot(self, *args, **kwargs):
        self.pv_mesh.plot(*args, **kwargs)

    @property
    def cells(self):
        # TODO: use meshios maps instead of iterating through vtk
        cell_list_connectivity = []
        start_index = 1

        cell_iterator = self.pv_mesh.NewCellIterator()
        cell_connectivity = self.pv_mesh.cells
        for _ in range(self.pv_mesh.n_cells):
            end_index = start_index + cell_iterator.GetNumberOfPoints()
            cell_list_connectivity.append(
                cell_connectivity[start_index:end_index])
            start_index = end_index + 1

        return pandas.DataFrame(cell_list_connectivity).add_prefix('point_')

    @property
    def points(self):
        return pandas.DataFrame(self.pv_mesh.points, columns=['x', 'y', 'z'])

    def _remove_invalid_cells(self):
        invalid_cell_indices = [
            i for i, cell_type in enumerate(self.pv_mesh.celltypes)
            if cell_type not in self.supported_cell_types]
        self.pv_mesh.remove_cells(invalid_cell_indices)

    @property
    def supported_cell_types(self):
        return [
            cell_type for cell_type, dimension
            in Map.cell_dimensions.items()
            if dimension == self.dimension]

    @property
    def bounds(self):
        return self.pv_mesh.bounds

    @utils.assign_parent
    def translate(self, direction, distance=None):
        direction = spatial.Direction(direction).scale(distance)

        copy = self.pv_mesh.copy(deep=True)
        copy.translate(direction)

        return self.__class__(copy)

    @utils.assign_parent
    def rotate(self, axis, angle):
        pass

    @utils.assign_parent
    def scale(self, reference, ratio):
        pass

    @utils.assign_parent
    def clip(self, surface, direction):
        pass

    @utils.assign_parent
    def cell_to_point(self):
        pass

    @utils.assign_parent
    def point_to_cell(self):
        pass

    @utils.assign_parent
    def flatten(self, plane=None):
        if plane is None:
            plane = spatial.Plane(origin=(0, 0, 0), normal=(0, 0, 1))

        flattened_mesh = (
            self.pv_mesh.extract_surface().project_points_to_plane(
                origin=plane.origin, normal=plane.orientation))

        return self.__class__(flattened_mesh)

    @utils.assign_parent
    def merge(self, *meshes):
        pv_mesh = self.pv_mesh
        for mesh in meshes:
            pv_mesh = pv_mesh.merge(mesh.pv_mesh)

        return self.__class__(pv_mesh)


class PointMesh(Mesh):
    dimension = 0

    @utils.assign_parent
    def extrude(self, direction, distance):
        pass


class LineMesh(Mesh):
    dimension = 1

    def _clean(self):
        return self.pv_mesh.extract_surface().clean()

    @utils.assign_parent
    def extrude(self, direction, distance=None):
        direction = spatial.Direction(direction).scale(distance)

        line = self._clean()
        extruded_surface = line.extrude(direction).triangulate()
        return SurfaceMesh(extruded_surface)

    @utils.assign_parent
    def extend(self, direction, distance=None):
        pass

    @utils.assign_parent
    def split(self, angle=90):
        # TODO: finish splitting alogirthm
        flattened_mesh = self.flatten()._clean()
        return flattened_mesh


class SurfaceMesh(Mesh):
    dimension = 2
    # TODO: add watertight attribute

    def _clean(self):
        return self.pv_mesh.extract_surface().clean()

    def _to_pymesh(self):
        return pymesh.form_mesh(self.points.values, self.cells.values)

    @utils.assign_parent
    def tetrahedral_mesh(self, **kwargs):
        # TODO: check if watertight
        # TODO: replace with CGAL to avoid AGPL
        tetrahedralizer = tetgen.TetGen(self._clean())
        tetrahedralizer.make_manifold()
        tetrahedralizer.tetrahedralize(**kwargs)
        return VolumeMesh(tetrahedralizer.grid)

    @utils.assign_parent
    def voxel_mesh(self, **kwargs):
        # TODO: check if watertight
        voxelized_mesh = pyvista.voxelize(self._clean(), **kwargs)
        return VolumeMesh(voxelized_mesh)

    @utils.assign_parent
    def boundary(self):
        boundary = self._clean().extract_feature_edges(
            manifold_edges=False, feature_edges=False)
        return LineMesh(boundary)

    @utils.assign_parent
    def extrude(self, direction, distance=None):
        direction = spatial.Direction(direction).scale(distance)
        boundary = self.boundary()

        extruded_surface = boundary.extrude(direction)
        translated_surface = self.translate(direction)

        return self.merge(extruded_surface, translated_surface)

    @utils.assign_parent
    def extend(self, direction, distance=None):
        pass

    @utils.assign_parent
    def clip_closed(self, plane=None, **kwargs):
        if plane is None:
            plane = spatial.Plane(**kwargs)

        vtk_plane = vtk.vtkPlane()
        vtk_plane.SetOrigin(*plane.origin)
        vtk_plane.SetNormal(*plane.orientation)

        plane_collection = vtk.vtkPlaneCollection()
        plane_collection.AddItem(vtk_plane)

        clipper = vtk.vtkClipClosedSurface()
        clipper.SetClippingPlanes(plane_collection)
        clipper.SetInputData(self._clean())
        clipper.Update()
        return SurfaceMesh.from_vtk(clipper.GetOutput())

    def _split_long_edges(self, max_length):
        mesh = pymesh.form_mesh(self.points.values, self.cells.values)
        split_mesh, _ = pymesh.split_long_edges(mesh, max_length)
        return create_mesh(split_mesh.vertices, split_mesh.faces)

    def _collapse_short_edges(self, min_length):
        mesh = pymesh.form_mesh(self.points.values, self.cells.values)
        collapsed_mesh, _ = pymesh.collapse_short_edges(
            mesh, min_length, preserve_feature=True)
        return create_mesh(collapsed_mesh.vertices, collapsed_mesh.faces)

    @utils.assign_parent
    def remesh(self, detail='low'):
        # TODO: rewrite
        # if size is None:
        #    cell_sizes = self.pv_mesh.compute_cell_sizes()
        #    size = average_cell_size = cell_sizes.cell_arrays['Area'].mean()

        return load_mesh(
            remesh.gen_remesh(self._to_pymesh(), detail=detail))


class VolumeMesh(Mesh):
    dimension = 3

    @utils.assign_parent
    def surface_mesh(self):
        return SurfaceMesh(self.pv_mesh.extract_surface().clean())


class Map:

    cell_dimensions = {
        0: None,  # empty
        1: 0,  # vertex
        2: 0,  # poly_vertex
        3: 1,  # line
        4: 1,  # poly_line
        5: 2,  # triangle
        6: 2,  # triangle_strip
        7: 2,  # polygon
        8: 2,  # pixel
        9: 2,  # quad
        10: 3,  # tetra
        11: 3,  # voxel
        12: 3,  # hexahedron
        13: 3,  # wedge
        14: 3,  # pyramid
        15: 3,  # penta_prism
        16: 3,  # hexa_prism
        21: 1,  # line3
        22: 2,  # triangle6
        23: 2,  # quad8
        24: 3,  # tetra10
        25: 3,  # hexahedron20
        26: 3,  # wedge15
        27: 3,  # pyramid13
        28: 2,  # quad9
        29: 3,  # hexahedron27
        30: 2,  # quad6
        31: 3,  # wedge12
        32: 3,  # wedge18
        33: 3,  # hexahedron24
        34: 2,  # triangle7
        35: 1,  # line4
        42: 3,  # polyhedron
    }

    dimension_classes = {
        0: PointMesh,
        1: LineMesh,
        2: SurfaceMesh,
        3: VolumeMesh,
    }


def dimension_class(dimension):
    return Map.dimension_classes[dimension]


def cell_dimension(cell_type):
    return Map.cell_dimensions[cell_type]


def create_mesh(points, cells, celltypes=None):
    # TODO: more efficient
    # TODO: add support for unstructured grids and points
    return load_mesh(pymesh.form_mesh(points, cells))


def load_mesh(unknown_mesh, dimension=None, **kwargs):
    # TODO: combine with Mesh classmethod constructors
    if isinstance(unknown_mesh, str):
        pv_mesh = pyvista.read_meshio(unknown_mesh, **kwargs)
    elif isinstance(unknown_mesh, pyvista.Common):
        pv_mesh = unknown_mesh
    elif isinstance(unknown_mesh, meshio.Mesh):
        pv_mesh = pyvista.from_meshio(unknown_mesh)
    elif isinstance(unknown_mesh, vtk.vtkDataSet):
        pv_mesh = pyvista.wrap(unknown_mesh)
    elif isinstance(unknown_mesh, Mesh):
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

    return dimension_class(dimension)(pv_mesh)


def _guess_mesh_dimension(pv_mesh):
    cell_dimensions = [
        cell_dimension(cell_type) for cell_type in pv_mesh.celltypes]
    dimension_count = Counter(cell_dimensions)
    return max(dimension_count, key=dimension_count.get)
