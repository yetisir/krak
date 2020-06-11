from abc import ABC, abstractmethod

import meshio
import pyvista


class Mesh(ABC):
    def __init__(
            self, mesh=None, file_name=None, file_type=None, **kwargs):

        if mesh:
            self._mesh = mesh
        elif file_name:
            self._mesh = pyvista.read_meshio(file_name, file_type)
        else:
            self._mesh = pyvista.from_meshio(meshio.Mesh(**kwargs))

        self._validate_mesh()

    @property
    @abstractmethod
    def dimension(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def supported_cell_types(self):
        raise NotImplementedError

    @property
    def cells(self):
        return self._mesh.cells

    @property
    def points(self):
        return self._mesh.points

    @property
    def cell_data(self):
        return self._mesh.cell_data

    @property
    def point_data(self):
        return self.point_data

    def _validate_mesh(self):
        valid_cell_indices = [
            i for i, cell_type in enumerate(self._mesh.celltypes)
            if cell_type in self.supported_cell_types]

        self._mesh = self._mesh.extract_cells(valid_cell_indices)

    def translate(self, direction, distance=None):
        pass

    def translate_x(self, distance):
        self.translate([1, 0, 0], distance)

    def translate_y(self, distance):
        self.translate([0, 1, 0], distance)

    def translate_z(self, distance):
        self.translate([0, 0, 1], distance)

    def rotate(self, axis, angle):
        pass

    def rotate_x(self, angle):
        self.rotate([1, 0, 0], angle)

    def rotate_y(self, angle):
        self.rotate([0, 1, 0], angle)

    def rotate_z(self, angle):
        self.rotate([0, 0, 1], angle)

    def scale(self, factor, reference):
        pass

    def scale_origin(self, factor):
        pass


class PointMesh(Mesh):
    dimension = 0
    supported_cell_types = [1, 2]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class LineMesh(Mesh):
    dimension = 1
    supported_cell_types = [3, 4]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class SurfaceMesh(Mesh):
    dimension = 2
    supported_cell_types = [5, 6, 7, 8, 9]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class VolumeMesh(Mesh):
    dimension = 3
    supported_cell_types = [10, 22, 12, 13, 14]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
