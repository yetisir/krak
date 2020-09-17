import numpy as np


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
    def __new__(cls, vector=None, trend=None, plunge=None, flip=False):
        assert (
            (vector is not None) or
            (trend is not None and plunge is not None)
        )

        if vector is None:
            trend_rad = np.deg2rad(trend)
            plunge_rad = np.deg2rad(plunge)
            vector = [
                np.sin(trend_rad) * np.cos(plunge_rad),
                np.cos(trend_rad) * np.cos(plunge_rad),
                -np.sin(plunge_rad),
            ]

        if flip:
            vector = [-i for i in vector]

        return super().__new__(cls, vector)

    @property
    def trend(self):
        if self[1] == 0:
            trend = 90 if self[0] > 0 else 270
        else:
            trend = np.rad2deg(np.arctan(self[0]/self[1]))
        return trend if trend > 0 else trend + 180

    @property
    def plunge(self):
        return np.rad2deg(-np.arcsin(self[-1] / np.linalg.norm(self)))

    def flip(self):
        return Direction(vector=self, flip=True)


class Orientation(Direction):
    def __new__(
            cls, normal=None, pole=None, strike=None, dip=None,
            dip_direction=None, plunge=None, trend=None, flip=True):
        assert (
            (normal is not None or pole is not None) or
            (strike is not None and dip is not None) or
            (dip is not None and dip_direction is not None)
            (trend is not None and plunge is not None)
        )

        if pole is not None:
            normal = pole
        if normal is None:
            if strike is not None:
                trend = strike - 90
            if dip is not None:
                plunge = 90 - dip
            if dip_direction is not None:
                trend = dip_direction + 180

        return super().__new__(
            cls, vector=normal, trend=trend, plunge=plunge, flip=flip)

    @property
    def strike(self):
        return self.trend + 90 if self.trend < 270 else self.trend - 270

    @property
    def dip(self):
        return 90 - self.plunge

    @property
    def dip_direction(self):
        return self.trend + 180 if self.trend < 180 else self.trend - 180

    def flip(self):
        return Orientation(normal=self, flip=True)


class Plane:
    def __init__(self, origin=None, orientation=None, **kwargs):
        self.origin = Position(origin)
        if orientation is None:
            orientation = Orientation(**kwargs)
        self.orientation = orientation

    @property
    def normal(self):
        return self.orientation

    @property
    def pole(self):
        return self.orientation

    def flip(self):
        return Plane(origin=self.origin, orientation=self.orientation.flip())


class Line:
    def __init__(self, origin=None, **kwargs):
        self.origin = Position(origin)
        self.direction = Direction(**kwargs)
