from collections import Counter
from abc import ABC, abstractmethod
import random
import re
from itertools import count

import meshio
import numpy as np
import pandas
import pymesh
import pyvista
import vtk
import ezdxf


from . import filters, viewer, spatial, metadata


class MeshFilters:
    def __init__(self):
        self.filters = {}
        for filter in self._all_filters(filters.Filter):
            if self.dimension not in filter.dimensions:
                continue
            filter_name = re.sub(
                r'(?<!^)(?=[A-Z])', '_', filter.__name__).lower()
            self.filters[filter_name] = filter
            self.add_filter(filter, filter_name)

    @property
    @abstractmethod
    def dimension(self):
        raise NotImplementedError

    def _all_filters(self, cls):
        return set(cls.__subclasses__()).union([
            subclass for filter_class in cls.__subclasses__() for
            subclass in self._all_filters(filter_class)
        ])

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

        self.cell_sets = metadata.CellSets(
            mesh_binding=self._binding)
        self.cell_fields = metadata.CellFields(
            mesh_binding=self._binding)
        self.properties = metadata.Properties(
            mesh_binding=self._binding)

        self.point_sets = metadata.PointSets(
            mesh_binding=self._binding)
        self.point_fields = metadata.PointFields(
            mesh_binding=self._binding)
        self.boundary_conditions = metadata.BoundaryConditions(
            mesh_binding=self._binding)

    def __hash__(self):
        return hash(str(self.serialize()))

    def __add__(self, other):
        return self.merge(other)

    def __sub__(self, other):
        pass

    @property
    @abstractmethod
    def dimension(self):
        raise NotImplementedError

    @staticmethod
    def load_mesh(*args, **kwargs):
        return load_mesh(*args, **kwargs)

    @staticmethod
    def load_points(*args, **kwargs):
        return load_points(*args, **kwargs)

    @staticmethod
    def load_lines(*args, **kwargs):
        return load_lines(*args, **kwargs)

    @staticmethod
    def load_surfaces(*args, **kwargs):
        return load_surfaces(*args, **kwargs)

    @staticmethod
    def load_volumes(*args, **kwargs):
        return load_volumes(*args, **kwargs)

    def _binding(self):
        return self

    @property
    def cells(self):
        # TODO: use meshios maps instead of iterating through vtk
        cell_list_connectivity = []
        start_index = 1

        cell_iterator = self.pyvista.NewCellIterator()
        cell_connectivity = self.pyvista.cells
        for _ in range(self.pyvista.number_of_cells):
            end_index = start_index + cell_iterator.GetNumberOfPoints()
            cell_list_connectivity.append(
                cell_connectivity[start_index:end_index])
            start_index = end_index + 1

        return pandas.DataFrame(
            cell_list_connectivity,
            index=pandas.RangeIndex(self.pyvista.number_of_cells)
        ).add_prefix('point_')

    @property
    def cell_centers(self):
        return pandas.DataFrame(
            self.pyvista.cell_centers().points, columns=['x', 'y', 'z'],
            index=pandas.RangeIndex(self.pyvista.number_of_cells)
        )

    @property
    def points(self):
        return pandas.DataFrame(
            self.pyvista.points, columns=['x', 'y', 'z'],
            index=pandas.RangeIndex(self.pyvista.number_of_points)
        )

    @property
    def supported_cell_types(self):
        return [
            cell_type for cell_type, dimension
            in Map.cell_dimensions.items()
            if dimension == self.dimension]

    @property
    def bounds(self):
        return pandas.DataFrame(
            np.array(self.pyvista.bounds).reshape((3, 2)),
            index=['x', 'y', 'z'],
            columns=['min', 'max'])

    @property
    def size(self):
        return self.bounds['max'] - self.bounds['min']

    @property
    def size_magnitude(self):
        return np.linalg.norm(self.size.values)

    @property
    def center(self):
        return self.pyvista.center

    def mesh_class(self, dimension=None, offset=0):
        if dimension is None:
            dimension = self.dimension
        return Map.dimension_classes[dimension + offset]

    @staticmethod
    def guess_dimension(pyvista):
        if not pyvista.number_of_cells:
            return None
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

    def plot(
            self, set=None, field=None, property=None,
            boundary_condition=None, **kwargs):
        if set is not None:
            scalars = f'set:{set}'
        elif field is not None:
            scalars = f'field:{field}'
        elif property is not None:
            scalars = f'property:{property}'
        elif boundary_condition is not None:
            scalars = f'bc:{boundary_condition}'
        else:
            scalars = None
        plotter = viewer.Window().plotter
        plotter.add_mesh(self.pyvista, scalars=scalars, **kwargs)
        # self.pyvista.plot(*args, **kwargs)

    def save(self, file_name):
        if file_name.endswith('dxf'):
            to_dxf(self, file_name)
        else:
            self.pyvista.save(file_name)

    def _remove_invalid_cells(self):
        if not self.pyvista.number_of_cells:
            return self
        invalid_cell_indices = [
            i for i, cell_type in enumerate(self.pyvista.celltypes)
            if cell_type not in self.supported_cell_types]
        self.pyvista.remove_cells(invalid_cell_indices)


class NullMesh(Mesh):
    dimension = None


class PointMesh(Mesh):
    dimension = 0


class LineMesh(Mesh):
    dimension = 1


class SurfaceMesh(Mesh):
    dimension = 2

    @property
    def normals(self):
        surface = self.pyvista.extract_surface()
        normals = surface.compute_normals(
            cell_normals=True, point_normals=False)
        return pandas.DataFrame(
            normals['Normals'],
            columns=['x', 'y', 'z'],
            index=pandas.RangeIndex(surface.number_of_cells)
        )

    @property
    def cell_areas(self):
        surface = self.pyvista.extract_surface()
        areas = surface.compute_cell_sizes(
            length=False,
            area=True,
            volume=False,
        )
        return pandas.DataFrame(
            areas['Area'],
            columns=['Area'],
            index=pandas.RangeIndex(surface.number_of_cells)
        )

    @property
    def manifold(self):
        return not bool(self.boundary().pyvista.number_of_cells)

    @property
    def watertight(self):
        return self.manifold

    @property
    def orientation(self):
        return spatial.Orientation(self.oriented_axes[-1])

    @property
    def oriented_axes(self):
        # There should be a more efficient way to calculate the OBB
        obb_tree = vtk.vtkOBBTree()
        obb_tree.SetDataSet(self.pyvista.extract_surface())
        obb_tree.BuildLocator()

        obb_surface = vtk.vtkPolyData()
        obb_tree.GenerateRepresentation(0, obb_surface)

        mesh = self.load_mesh(obb_surface)
        normals = mesh.normals.values
        areas = mesh.cell_areas['Area'].values

        all_normals = []
        for normal, area in zip(normals, areas):
            normal = spatial.Direction(normal).scale(area)
            if normal[0] < 0:
                normal = normal.flip()

            if normal not in all_normals:
                all_normals.append(normal)

        sorted_normals = sorted(
            all_normals, key=lambda normal: normal.magnitude)
        return [normal.unit for normal in sorted_normals]

    def _to_pymesh(self):
        return pymesh.form_mesh(self.points.values, self.cells.values)


class VolumeMesh(Mesh):
    dimension = 3


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


def from_dxf(file_name):
    dxf_surface = ezdxf.readfile(file_name)

    points = vtk.vtkPoints()
    cells = vtk.vtkCellArray()
    mesh = vtk.vtkPolyData()

    point_id = 0
    for entity in dxf_surface.entities:
        entity_type = entity.dxftype()
        point_id_list = vtk.vtkIdList()

        if entity_type == '3DFACE':
            dxf_points = [getattr(entity.dxf, f'vtx{i}') for i in range(4)]

        elif entity_type == 'POLYLINE':
            dxf_points = [vertex.dxf.location for vertex in entity.vertices]

        elif entity_type == 'LWPOLYLINE':
            dxf_points = [
                vertex[:2] + (entity.dxf.elevation, )
                for vertex in entity.get_points()]
        else:
            dxf_points = []

        for dxf_point in dxf_points:
            points.InsertPoint(point_id, dxf_point)
            point_id_list.InsertNextId(point_id)
            point_id += 1

        cells.InsertNextCell(point_id_list)

    mesh.SetPoints(points)
    mesh.SetPolys(cells)

    return mesh


def to_dxf(pyvista_mesh, file_name):
    pass


def to_pyvista(unknown_mesh):
    if isinstance(unknown_mesh, str):
        if unknown_mesh.endswith('dxf'):
            pv_mesh = pyvista.wrap(from_dxf(unknown_mesh))
        else:
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
        if dimension is None:
            raise ValueError(
                'No valid cells or points found in mesh. '
                'Cannot determine dimension')

    return Map.dimension_classes[dimension](pv_mesh)


def load_points(points):
    return load_mesh(pyvista.PolyData(np.array(points)))


def load_lines(points, connectivity):
    cells = []
    for cell in connectivity:
        cells.append(len(cell))
        cells.extend(cell)

    pv_mesh = pyvista.PolyData()
    pv_mesh.points = np.array(points)
    pv_mesh.lines = np.array(cells)
    return load_mesh(pv_mesh, dimension=1)


def load_surfaces(points, connectivity):
    cells = []
    for cell in connectivity:
        cells.append(len(cell))
        cells.extend(cell)

    pv_mesh = pyvista.PolyData(np.array(points), np.array(cells))
    return load_mesh(pv_mesh, dimension=2)


def load_volumes(points, element_type, connectivity):
    raise NotImplementedError
