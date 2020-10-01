from abc import ABC  # , abstractmethod


class BaseRange(ABC):
    def __add__(self, other):
        return Union(self, other)

    def __sub__(self, other):
        return Intersection(self, Invert(other))

    def __neg__(self):
        return Invert(self)


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


class Group(BaseRange):
    def query(self, mesh, component):
        pass


class Id(BaseRange):
    pass


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

        component_coordinates = component_positions[component_positions.columns[self.coordinate]]
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
