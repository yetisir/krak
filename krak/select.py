from abc import ABC  # , abstractmethod

import numpy as np
import vtk
from tqdm import tqdm

from . import spatial


class BaseRange(ABC):
    def __add__(self, other):
        return Union(self, other)

    def __sub__(self, other):
        return Intersection(self, Invert(other))

    def __neg__(self):
        return Invert(self)

    def map_points_to_cells(self, point_array, mesh):
        array_name = 'temp:range'
        mesh.pyvista.point_arrays[array_name] = point_array
        return mesh.pyvista.point_data_to_cell_data().cell_arrays[array_name]

    def map_cells_to_points(self, cell_array, mesh):
        array_name = 'temp:range'
        mesh.pyvista.cell_arrays[array_name] = cell_array
        return mesh.pyvista.cell_data_to_point_data().point_arrays[array_name]


class Union(BaseRange):
    pass


class Intersection(BaseRange):
    pass


class Invert(BaseRange):
    pass


class All(BaseRange):
    def query(self, mesh, component):
        if component == 'cells':
            return mesh.cells.index.values
        elif component == 'points':
            return mesh.points.index.values
        elif component == 'faces':
            pass  # TODO: implement face logic


class Null(BaseRange):
    def query(self, mesh, component):
        pass


class Set(BaseRange):
    def query(self, mesh, component):
        pass


class Ids(BaseRange):
    def __init__(self, ids):
        self.ids = ids

    def query(self, mesh, component):
        if component == 'cells':
            ids = mesh.cells.index
        elif component == 'points':
            ids = mesh.points.index

        return ids.to_series().isin(self.ids).values


class CoordinateRange(BaseRange):
    def __init__(self, coordinate_range, coordinate, tolerance=1e-6):
        coordinate_range = list(coordinate_range)
        range_length = len(coordinate_range)
        if range_length == 0:
            raise ValueError('At least one coordinate value must be specified')
        elif range_length == 1:
            coordinate_range = coordinate_range * 2
        elif range_length > 2:
            raise ValueError(
                'No more than 2 coordinate values may be specified')

        if coordinate_range[0] is None:
            coordinate_range[0] = float('-inf')
        if coordinate_range[1] is None:
            coordinate_range[1] = float('inf')

        self.coordinate_range = coordinate_range
        self.coordinate = coordinate
        self.tolerance = tolerance

    def query(self, mesh, component):
        coordinate_range = self.coordinate_range.copy()
        for i, coordinate in enumerate(self.coordinate_range):
            if coordinate == 'min':
                coordinate_range[i] = mesh.bounds[self.coordinate][0]
            elif coordinate == 'max':
                coordinate_range[i] = mesh.bounds[self.coordinate][1]

        coordinate_range[0] -= self.tolerance
        coordinate_range[1] += self.tolerance

        if component == 'cells':
            component_positions = mesh.cell_centers

        if component == 'points':
            component_positions = mesh.points

        component_coordinates = (
            component_positions[component_positions.columns[self.coordinate]]
        )
        return (
            (component_coordinates >= coordinate_range[0]) &
            (component_coordinates <= coordinate_range[1])
        ).values


class PositionX(CoordinateRange):
    def __init__(self, *coordinate_range, **kwargs):
        super().__init__(coordinate_range, coordinate=0, **kwargs)


class PositionY(CoordinateRange):
    def __init__(self, *coordinate_range, **kwargs):
        super().__init__(coordinate_range, coordinate=1, **kwargs)


class PositionZ(CoordinateRange):
    def __init__(self, *coordinate_range, **kwargs):
        super().__init__(coordinate_range, coordinate=2, **kwargs)


class Distance(BaseRange):
    def __init__(self, mesh, distance):
        self.mesh = mesh
        self.distance = distance

    def query(self, mesh, component):

        surface_distance_function = vtk.vtkImplicitPolyDataDistance()
        surface_distance_function.SetInput(self.mesh.pyvista.extract_surface())

        surface_distances = np.empty(mesh.pyvista.GetNumberOfPoints())

        points = mesh.pyvista.GetPoints()
        for i in tqdm(range(mesh.pyvista.GetNumberOfPoints())):
            distance = surface_distance_function.EvaluateFunction(
                points.GetPoint(i))
            surface_distances[i] = abs(distance)

        if component == 'points':
            return surface_distances <= self.distance

        elif component == 'cells':
            return self.map_points_to_cells(
                surface_distances, mesh) <= self.distance


class RayCount(BaseRange):
    def __init__(self, mesh, count, direction=None, **kwargs):
        self.mesh = mesh
        self.direction = spatial.Direction(vector=direction, **kwargs)

    def query(self, mesh, component):
        pass
