from collections import Counter
from abc import ABC, abstractmethod
import traceback
import random
import re
from itertools import count

import meshio
import numpy as np
import pandas
import pymesh
import pyvista
import vtk


from . import spatial, utils, filters


class MeshFilters:
    def __init__(self):
        self.filters = {}
        for filter in filters.Filter.__subclasses__():
            if self.dimension not in filter.dimensions:
                continue
            filter_name = re.sub(
                r'(?<!^)(?=[A-Z])', '_', filter.__name__).lower()
            self.filters[filter_name] = filter
            self.add_filter(filter, filter_name)

    def add_filter(self, filter, name):
        setattr(
            self, name,
            lambda *args, **kwargs: filter(self, *args, **kwargs).filter())


class Mesh(MeshFilters, ABC):
    _registry = []
    _count = count(1)

    def __init__(self, mesh, parents=None, register=True, name=None):
        super().__init__()
        if name is not None:
            if name not in [obj.name for obj in self._registry]:
                self.name = name
            else:
                raise ValueError('Name already taken')
        else:
            # TODO: better naming
            number = next(self._count)
            self.name = f'{self.__class__.__name__}_{number}'

        self.id = hash(random.random())

        mesh = to_pyvista(mesh)

        self.pyvista = mesh.cast_to_unstructured_grid()

        if parents is None:
            self.parents = []
        else:
            self.parents = list(parents)
        self._remove_invalid_cells()

        if register:
            self._registry.append(self)

    def __add__(self, other):
        return self.merge(other)

    def __sub__(self, other):
        pass

    @property
    @abstractmethod
    def dimension(self):
        raise NotImplementedError

    @property
    def cells(self):
        # TODO: use meshios maps instead of iterating through vtk
        cell_list_connectivity = []
        start_index = 1

        cell_iterator = self.pyvista.NewCellIterator()
        cell_connectivity = self.pyvista.cells
        for _ in range(self.pyvista.n_cells):
            end_index = start_index + cell_iterator.GetNumberOfPoints()
            cell_list_connectivity.append(
                cell_connectivity[start_index:end_index])
            start_index = end_index + 1

        return pandas.DataFrame(cell_list_connectivity).add_prefix('point_')

    @property
    def points(self):
        return pandas.DataFrame(self.pyvista.points, columns=['x', 'y', 'z'])

    @property
    def supported_cell_types(self):
        return [
            cell_type for cell_type, dimension
            in Map.cell_dimensions.items()
            if dimension == self.dimension]

    @property
    def bounds(self):
        return self.pyvista.bounds

    def mesh_class(self, dimension=None, offset=0):
        if dimension is None:
            dimension = self.dimension
        return Map.dimension_classes[dimension + offset]

    @staticmethod
    def guess_dimension(pyvista):
        cell_dimensions = [
            cell_dimension(cell_type) for cell_type in pyvista.celltypes]
        dimension_count = Counter(cell_dimensions)
        return max(dimension_count, key=dimension_count.get)

    def serialize(self):
        # TODO: serialize more efficiently

        return {
            'dimension': self.dimension,
            'name': self.name,
            'id': self.id,
            'parents': [parent.id for parent in self.parents],
            'points': self.points.values.tolist(),
            'point_arrays': {
                key: value.tolist() for key, value
                in self.pyvista.point_arrays.items()},
            'cells': self.pyvista.cells.tolist(),
            'celltypes': self.pyvista.celltypes.tolist(),
            'offset': self.pyvista.offset.tolist(),
            'cell_arrays': {
                key: value.tolist() for key, value
                in self.pyvista.cell_arrays.items()},
        }

    def cell_to_point(self):
        pass

    def point_to_cell(self):
        pass

    def plot(self, *args, **kwargs):
        self.pyvista.plot(*args, **kwargs)

    def _remove_invalid_cells(self):
        invalid_cell_indices = [
            i for i, cell_type in enumerate(self.pyvista.celltypes)
            if cell_type not in self.supported_cell_types]
        self.pyvista.remove_cells(invalid_cell_indices)


class PointMesh(Mesh):
    dimension = 0


class LineMesh(Mesh):
    dimension = 1


class SurfaceMesh(Mesh):
    dimension = 2

    @property
    def manifold(self):
        raise NotImplementedError

    @property
    def watertight(self):
        # alias for manifold
        return self.manifold

    def _to_pymesh(self):
        return pymesh.form_mesh(self.points.values, self.cells.values)


class VolumeMesh(Mesh):
    dimension = 3

    # @utils.assign_parent
    # def surface_mesh(self):
    #     return SurfaceMesh(self.pyvista.extract_surface().clean())


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


def cell_dimension(cell_type):
    return Map.cell_dimensions[cell_type]


def create_mesh(points, cells, celltypes=None):
    # TODO: more efficient
    # TODO: add support for unstructured grids and points
    return load_mesh(pymesh.form_mesh(points, cells))


def to_pyvista(unknown_mesh):
    if isinstance(unknown_mesh, str):
        pv_mesh = pyvista.read_meshio(unknown_mesh)
    elif isinstance(unknown_mesh, pyvista.Common):
        pv_mesh = unknown_mesh
    elif isinstance(unknown_mesh, meshio.Mesh):
        pv_mesh = pyvista.from_meshio(unknown_mesh)
    elif isinstance(unknown_mesh, vtk.vtkDataSet):
        pv_mesh = pyvista.wrap(unknown_mesh)
    elif isinstance(unknown_mesh, Mesh):
        pv_mesh = unknown_mesh.pyvista
    elif isinstance(unknown_mesh, pymesh.Mesh):
        # TODO: handle line and volume cells
        cell_array = []
        for cell in unknown_mesh.faces:
            cell_array.append(len(cell))
            cell_array.extend(cell)
        pv_mesh = pyvista.PolyData(
            unknown_mesh.vertices, np.array(cell_array))
    elif isinstance(unknown_mesh, dict):
        pass

    return pv_mesh


def load_mesh(mesh, dimension=None):

    pv_mesh = to_pyvista(mesh).cast_to_unstructured_grid()
    if dimension is None:
        dimension = Mesh.guess_dimension(pv_mesh)

    return Map.dimension_classes[dimension](pv_mesh)
