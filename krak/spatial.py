import numpy as np

# TODO: look into using existing library for the basis of these data structures


class Vector(np.ndarray):
    # TODO: add error checking on vector
    def __new__(cls, vector):
        assert len(vector) == 3

        return np.array(vector).view(cls)

    def scale(self, size):
        if size is None:
            return self
        return self.__class__(self.unit * size)

    @property
    def unit(self):
        return self.__class__(self / self.magnitude)

    @property
    def values(self):
        return np.array(self)

    @property
    def magnitude(self):
        return np.linalg.norm(self)


class Position(Vector):
    pass


class Direction(Vector):
    def __new__(cls, vector=None, trend=None, plunge=None):
        if vector is None:
            # TODO: write function
            pass
        return super().__new__(cls, vector)

    @property
    def trend(self):
        pass

    @property
    def plunge(self):
        pass


class Orientation(Vector):
    def __new__(
            cls, normal=None, strike=None, dip=None, dip_direction=None,
            **kwargs):
        if normal is None:
            # TODO: write function
            pass
        return super().__new__(cls, normal)

    @property
    def strike(self):
        pass

    @property
    def dip(self):
        pass

    @property
    def dip_direction(self):
        pass

    @property
    def pole(self):
        return self.normal

    def flip(self):
        pass


class Plane:
    def __init__(self, origin=None, **kwargs):
        self.origin = Position(origin)
        self.orientation = Orientation(**kwargs)

    @property
    def normal(self):
        # alias for orientation
        return self.orientation

class Line:
    def __init__(self, origin=None, **kwargs):
        self.origin = Position(origin)
        self.direction = Direction(**kwargs)
