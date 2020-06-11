from abc import ABC, abstractmethod

import pyvista
import pandas

from . import common


class Mesh(ABC):
    def __init__(self, mesh):
        super().__init__()
        self.pv_mesh = self._get_valid_mesh(mesh)

    @classmethod
    def from_file(cls, file_name, file_type=None):
        return cls(pyvista.read_meshio(file_name, file_type))

    @classmethod
    def from_pyvista(cls, mesh):
        return cls(mesh)

    @classmethod
    def from_vtk(cls, mesh):
        raise NotImplementedError

    @classmethod
    def from_meshio(cls, mesh):
        return cls(pyvista.from_meshio(mesh))

    @property
    @abstractmethod
    def dimension(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def supported_cell_types(self):
        raise NotImplementedError

    def cells(self):
        pass

    def points(self):
        return pandas.DataFrame(self.pv_mesh.points, columns=['x', 'y', 'z'])

    def _get_valid_mesh(self, pv_mesh):
        valid_cell_indices = [
            i for i, cell_type in enumerate(pv_mesh.celltypes)
            if cell_type in self.supported_cell_types]

        return pv_mesh.extract_cells(valid_cell_indices)

    @property
    def supported_cell_types(self):
        return [
            cell_type for cell_type, dimension
            in Map.cell_dimensions.items()
            if dimension == self.dimension]

    @property
    def bounds(self):
        return self.pv_mesh.bounds


    def rotate(self, axis, angle):
        pass

    def scale(self, reference, ratio):
        pass

    def clip(self, surface, direction):
        pass

    def cell_to_point(self):
        pass

    def point_to_cell(self):
        pass

class PointMeshFilters:
    pass

class LineMeshFilters:
    pass

class SurfaceMeshFilters:
    pass

class VolumeMeshFilters:
    pass


class PointMesh(Mesh):
    dimension = 0


class LineMesh(Mesh):
    dimension = 1


class SurfaceMesh(Mesh):
    dimension = 2


class VolumeMesh(Mesh):
    dimension = 3

    def extract_surface(self):
        return SurfaceMesh(self.pv_mesh.extract_surface)

class Map:
    cell_dimensions = {
        1: 0,
        2: 0,
        3: 1,
        4: 1,
        5: 2,
        6: 2,
        7: 2,
        8: 2,
        9: 2,
        10: 3,
        11: 3,
        12: 3,
        13: 3,
        14: 3,
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

