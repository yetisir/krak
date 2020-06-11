from abc import ABC, abstractmethod

import pyvista


class Mesh(ABC):
    def __init__(self, mesh):
        super().__init__()
        self.mesh = self._get_valid_mesh(mesh)

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

    def _get_valid_mesh(self, mesh):
        valid_cell_indices = [
            i for i, cell_type in enumerate(mesh.celltypes)
            if cell_type in self.supported_cell_types]

        return mesh.extract_cells(valid_cell_indices)

    @property
    def bounds(self):
        return self.mesh.bounds

    def max_bound(self, dimension):
        if dimension in [0, 'x']:
            return self.bounds[1]
        elif dimension in [1, 'y']:
            return self.bounds[3]
        elif dimension in [2, 'z']:
            return self.bounds[5]

    def min_bound(self, dimension):
        if dimension in [0, 'x']:
            return self.bounds[0]
        elif dimension in [1, 'y']:
            return self.bounds[2]
        elif dimension in [2, 'z']:
            return self.bounds[4]


    def translate(self, direction, distance=None):
        pass

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


class PointMesh(Mesh):
    dimension = 0
    supported_cell_types = [1, 2]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class LineMesh(Mesh):
    dimension = 1
    supported_cell_types = [3, 4]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)



class SurfaceMesh(Mesh):
    dimension = 2
    supported_cell_types = [5, 6, 7, 8, 9]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class VolumeMesh(Mesh):
    dimension = 3
    supported_cell_types = [10, 22, 12, 13, 14]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def extract_surface(self):
        pass
