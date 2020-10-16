"""Module providing vector utilities for geoscience applications.

This module contains classes that can help simplify the description and
manipulation of spatial positions, directions, and orientations. Specifically,
it allows the description of the quantities in terms of standard geoscience
quantities such as strike, dip, trend and plunge, but also allows for standard
mathematical descriptions.

    # Define a vector by trend and plunge
    vector = spatial.Vector(trend=13, plunge=40)
    print(vector)
    >>> Vector([ 0.17232251,  0.74641077, -0.64278761])

    # Define a plane orientation by the plane normal
    orientation = spatial.Orientation(normal=(13.9, 7.6, 23.0))
    print(orientation)
    >>> Orientation([13.9,  7.6, 23. ])

    # Project the vector onto the plane orientation
    projection = vector.project(orientation)
    print(projection)
    >>> Vector([ 0.29201164,  0.81185231, -0.44474084])
"""


import numpy as np

from . import properties, units


class BaseVector(np.ndarray):
    """Base spatial vector quantity, inherited from np.ndarray.

    Vector objects inherit from np.ndarray, but are constrained to a length
    of 3 and have overloaded operators to make vector operations easier.
    Scaling and projection methods have also been added for convenience.

    Attributes:
        unit (krak.spatial.Vector):
            A unit vector of the same type. i.e. scaled to a magnitude of 1.
        values (np.ndarray):
            The underlying np.ndarray.
        magnitude (float):
            The algebraic norm of the vector.

    Todo:
        Add better support and distinction for 2 dimensional vectors?
    """

    def __new__(cls, vector=(0, 0, 1)):
        """Creates an Vector object given a 2 or three dimensional vector.

        Args:
            vector (array_like):
                Numeric array of length 2 or 3 representing a vector quantity
        """

        return cls._validate_vector(vector).view(cls)

    def __mul__(self, other):
        return np.dot(self, other * 1)

    def __pow__(self, other):
        return Orientation(normal=np.cross(self, other))

    def __rshift__(self, other):
        return self.project(other)

    def __lshift__(self, other):
        return other.project(self)

    def __eq__(self, other):
        try:
            other = Vector(other)
        except TypeError:
            return False

        if np.sign(self[0]) != np.sign(other[0]):
            print(3)
            return False

        if not np.isclose(self.magnitude, other.magnitude):
            print(4)
            return False

        if self.magnitude == 0 and other.magnitude == 0:
            return True

        if not np.isclose(self.unit * other.unit, 1):
            print(5)
            return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def x(self):
        return self[0]

    @x.setter
    def x(self, value):
        self[0] = value

    @property
    def y(self):
        return self[1]

    @y.setter
    def y(self, value):
        self[1] = value

    @property
    def z(self):
        return self[2]

    @z.setter
    def z(self, value):
        self[2] = value

    @property
    def unit(self):
        """Scales vector to a magnitude of 1. This method creates a new
        Vector object and does not mutate the original Vector object.

        Returns:
            krak.spatial.Vector:
                New Vector object with magnitude of 1.
        """
        if self.magnitude:
            unit_vector = self / self.magnitude
        else:
            unit_vector = self
        return self.__class__(unit_vector)

    @property
    def values(self):
        """Accessor for underlying numpy array

        Returns:
            np.ndarray:
                Underlying numpy array.
        """

        return np.array(self)

    @values.setter
    def values(self, value):
        vector = self._validate_vector(value)
        for i, component in enumerate(vector):
            self[i] = component

    @property
    def magnitude(self):
        """Algebraic norm of the vector

        Returns:
            float:
                Vector magnitude
        """

        return np.linalg.norm(self)

    @magnitude.setter
    def magnitude(self, value):
        self.values = self.scale(value)

    def scale(self, size):
        """Scales vector to a specified magnitude. This method creates a new
        Vector object and does not mutate the original Vector object.

        Args:
            size (float):
                Desired magnitude of the resultant vector.

        Returns:
            krak.spatial.Vector:
                New Vector object with specified magnitude.
        """

        if size is None:
            return self
        return self.__class__(self.unit * size)

    def flip(self):
        return self.__class__(-self)

    @staticmethod
    def _validate_vector(vector):
        try:
            length = len(vector)
        except TypeError:
            raise TypeError('Vector must be array-like')

        if length == 2:
            vector = list(vector) + [0]
        if length != 3:
            raise ValueError('Vector must be length 2 or 3')

        try:
            return np.array(vector, dtype=float)
        except ValueError:
            raise ValueError('Vector must be numeric')


class Vector(BaseVector):
    """Vector used to describe a direction without a positional reference.

    Vector objects inherit from Vector objects and add new ways to
    construct based on conventional geoscience nomenclature and conventions.
    Here, trend and plunge are offered as arguments to help simplify the
    vector description. An optional flip argument is also provided to reverse
    the direction of the vector during intialization.

    Attributes:
        trend (float):
            Azimuth of the horizontal component of the direction.
        plunge (float):
            Inclination of vector from the horizontal.

    Todo:
        Add support for unit quantities (i.e. degrees adn radians for
        trend and plunge)

    """

    def __new__(cls, vector=None, trend=None, plunge=None):
        """Creates a Vector object given either a vector array or trend
        and plunge.

        Args:
            vector (array_like):
                Numeric array of length 2 or 3 representing a vector quantity
            trend (float):
                Azimuth of the horizontal component of the direction (degrees).
            plunge (float):
                Inclination of vector from the horizontal (degrees).
        """

        if vector is None:
            vector = cls._vector_from_trend_and_plunge(trend, plunge)

        return super().__new__(cls, vector)

    @property
    def trend(self):
        """Azimuth of the horizontal component of the direction (degrees).

        Returns:
            float:
                trend of the vector (degrees)
        """

        if self.y == 0:
            trend = 90 if self.x > 0 else 270
        else:
            trend = np.rad2deg(np.arctan(self.x / self.y))

        return trend if trend > 0 else trend + 180

    @trend.setter
    def trend(self, trend):
        self.values = self._vector_from_trend_and_plunge(trend, self.plunge)

    @property
    def plunge(self):
        """Inclination of vector from the horizontal (degrees).

        Returns:
            float:
                plunge of the vector (degrees)
        """

        return np.rad2deg(-np.arcsin(self[-1] / np.linalg.norm(self)))

    @plunge.setter
    def plunge(self, plunge):
        self.values = self._vector_from_trend_and_plunge(self.trend, plunge)

    def project(self, destination):
        """Projects vector onto any krak.spatial Object and Returns a new
        Vector object. Valid destinations include all vector and plane like
        quantities. Projection onto a plane or orientation is done in the
        normal direction.

        Args:
            destination (krak.spatial Object):
                Spatial object to project vector onto.

        Returns:
            krak.spatial.Vector:
                Projected vector object of the same type.
        """

        if isinstance(destination, Vector):
            return self._vector_projection(Vector(destination))
        elif isinstance(destination, Orientation):
            return Vector(self - (self >> destination.normal))

        elif isinstance(destination, Line):
            return Line(
                origin=destination.origin,
                direction=self >> destination.direction)
        elif isinstance(destination, Plane):
            return Line(
                origin=destination.origin,
                direction=self >> destination.orientation)
        else:
            try:
                return self._vector_projection(Vector(destination))
            except TypeError:
                raise ValueError(f'Unable to project onto "{destination}"')

    @staticmethod
    def _vector_from_trend_and_plunge(trend, plunge):
        trend = (
            properties.Trend(trend).quantity if trend is not None else
            0 * units.Unit('deg'))
        plunge = (
            properties.Plunge(plunge).quantity if plunge is not None else
            -90 * units.Unit('deg'))

        return [
            np.sin(trend).magnitude * np.cos(plunge).magnitude,
            np.cos(trend).magnitude * np.cos(plunge).magnitude,
            -np.sin(plunge).magnitude,
        ]

    def _vector_projection(self, destination):
        return Vector(
            destination.unit * np.dot(self, destination) /
            destination.magnitude)


class Orientation(BaseVector):
    def __new__(
            cls, normal=None, pole=None, strike=None, dip=None,
            dip_direction=None, plunge=None, trend=None):

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

            normal = Vector(trend=trend, plunge=plunge)

        return super().__new__(cls, vector=normal)

    @property
    def strike(self):
        return self.trend + 90 if self.trend < 270 else self.trend - 270

    @property
    def dip(self):
        return 90 - self.plunge

    @property
    def dip_direction(self):
        return self.trend + 180 if self.trend < 180 else self.trend - 180

    @property
    def normal(self):
        return Vector(self)


class Line:
    def __init__(self, origin=None, **kwargs):
        self.origin = Vector(origin)
        self.direction = Vector(**kwargs)

    def __rshift__(self, other):
        return self.project(self, other)

    def project(self, destination):
        return Line(
            origin=self.origin >> destination,
            direction=self.direction >> destination,
        )


class Plane:
    def __init__(self, origin=None, orientation=None, **kwargs):
        self.origin = Vector(origin)
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
