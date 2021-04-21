"""Module providing vector utilities for geoscience applications.

This module contains classes that can help simplify the description and
manipulation of spatial positions, directions, and orientations. Specifically,
it allows the description of the quantities in terms of standard geoscience
quantities such as strike, dip, trend and plunge, but also allows for standard
mathematical descriptions.
"""


import numpy as np
import pyvista as pv

from . import properties, units, config, viewer


class Vector(np.ndarray):
    """Vector used to describe a direction without a positional reference.

    Vector objects inherit from np.ndarray, but are constrained to a length
    of 3 and have overloaded operators to make vector operations easier. 2D
    vectors are supported by adding a z component = 0 which forces all
    operations onto the xy plane. Scaling and projection methods have also been
    added for convenience. Object construction can be based on conventional
    geoscience nomenclature and conventions such as trend and plunge to help
    simplify the vector description.

    Attributes:
        unit (krak.spatial.Vector):
            A unit vector of the same type. i.e. scaled to a magnitude of 1.
        values (np.ndarray):
            The underlying np.ndarray. (settable)
        magnitude (float):
            The algebraic norm of the vector. (settable)
        trend (float):
            Azimuth of the horizontal component of the direction. (settable)
        plunge (float):
            Inclination of vector from the horizontal. (settable)
        x (float):
            x coordinate of the vector (settable)
        y (float):
            y coordinate of the vector (settable)
        z (float):
            z coordinate of the vector (settable)

    Todo:
        Add better support and distinction for 2 dimensional vectors?
        move static methods outside of class
    """

    def __new__(cls, vector=None, direction=None, trend=None, plunge=None):
        """Creates a Vector object given either a vector array or trend
        and plunge.

        Args:
            vector (array_like, optional):
                Numeric array of length 2 or 3 representing a vector quantity
            direction (array_like, optional):
                Alias for vector
            trend (float, optional):
                Azimuth of the horizontal component of the direction (degrees).
            plunge (float, optional):
                Inclination of vector from the horizontal (degrees).
        """

        if direction is not None:
            vector = direction

        if vector is None:
            vector = cls._vector_from_trend_and_plunge(trend, plunge)

        return cls._validate_vector(vector).view(cls)

    def __mul__(self, other):
        return np.dot(self, other * 1)

    def __pow__(self, other):
        return Orientation(normal=np.cross(self, other))

    def __rshift__(self, other):
        return self.project(other)

    def __eq__(self, other):
        try:
            other = Vector(other)
        except TypeError:
            return False

        return np.isclose(self.values, other.values).all()

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def x(self):
        """Get the x component of the vector

        Returns:
            float: x component of the vector
        """

        return self[0]

    @x.setter
    def x(self, value):
        """Get the x component of the vector

        Args:
            value (float): x component of the vector
        """

        self[0] = value

    @property
    def y(self):
        """Get the y component of the vector

        Returns:
            float: y component of the vector
        """

        return self[1]

    @y.setter
    def y(self, value):
        """Get the y component of the vector

        Args:
            value (float): y component of the vector
        """

        self[1] = value

    @property
    def z(self):
        """Get the z component of the vector

        Returns:
            float: z component of the vector
        """

        return self[2]

    @z.setter
    def z(self, value):
        """Get the z component of the vector

        Args:
            value (float): z component of the vector
        """

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
        """Setter for underlying numpy array values

        Args:
            value (array-like):  array of length 2 or 3
        """

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
        """Sets the vector magnitude by scaling it.

        Args:
            value (float): Desired vector magnitude
        """

        self.values = self.scale(value)

    @property
    def trend(self):
        """Azimuth of the horizontal component of the direction (degrees).

        Returns:
            float:
                trend of the vector (degrees)
        """

        trend = np.arctan2(self.x, self.y) * units.Unit('rad')
        trend = trend if trend > 0 else trend + 360 * units.Unit('deg')

        return trend.to(config.settings.units.angle)

    @trend.setter
    def trend(self, trend):
        """sets the trend of the vector in place. The current plunge of the
        vector is maintained.

        Args:
            trend (float):
                azimuth of the vector trend. krak.Units are supported, and
                will revert to default units in krak.settings if not specified.
        """

        self.values = self._vector_from_trend_and_plunge(trend, self.plunge)

    @property
    def plunge(self):
        """Inclination of vector from the horizontal (degrees).

        Returns:
            float:
                plunge of the vector (degrees)
        """

        plunge = -np.arcsin(self.z / self.magnitude) * units.Unit('rad')

        return plunge.to(config.settings.units.angle)

    @plunge.setter
    def plunge(self, plunge):
        """Sets the plunge of the vector in place. The current trend of the
        vector is maintained.

        Args:
            plunge (float):
                Angle of vector plunge. krak.Units are supported, and
                will revert to default units in krak.settings if not specified.
        """

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

        if isinstance(destination, Orientation):
            return Vector(self - (self >> destination.normal))
        elif isinstance(destination, Vector):
            return self._vector_projection(Vector(destination))

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
        """Reverses the direction of the spatial quantity.
        A new Vector object is returned.

        Returns:
            krak.Spatial.Vector:
                Same vector but reversed
        """
        return self.__class__(-self)

    def plot(self, origin=(0, 0, 0), **kwargs):
        """Creates a visual representation of the vector and plots it to the
        active canvas.

        Args:
            origin (tuple, optional):
                Position of the base of the vector representation.
                Defaults to (0, 0, 0).
        """

        plotter = viewer.Window()
        arrow = pv.Arrow(start=np.array(origin), direction=self.values)
        plotter.add_mesh(arrow, **kwargs)

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


class Orientation(Vector):
    """Special type of Vector used to describe a plane without a positional
    reference.

    An Orientation object describes a plane without any positional reference
    as a plane normal. Internaly the Orientation class inherits from
    np.ndarray and krak.spatial.Vector.

    Attributes:
        normal (array_like):
            Vector representing the plane normal. (settable)
        pole (array_like):
            Vector representing the plane pole (analagous to normal).
            (settable)
        strike (float):
            Strike of the plane. Units may be specified, otherwise
            defaults to default unit system. (settable)
        dip (float):
            Dip of the plane. Units may be specified, otherwise
            defaults to default unit system. (settable)
        dip_direction (float):
            Dip direction of the plane. Units may be specified, otherwise
            defaults to default unit system. (settable)
        plunge (float):
            Plunge of the plane. Units may be specified, otherwise
            defaults to default unit system. (settable)
        trend (float):
            Trend of the plane. Units may be specified, otherwise
            defaults to default unit system. (settable)
    """

    def __new__(
            cls, normal=None, pole=None, strike=None, dip=None,
            dip_direction=None, plunge=None, trend=None):
        """Creates an Orientation Object. An Orientation describes a plane
        without any positional reference. Internaly the Orientation class
        inherits from np.ndarray and krak.spatial.Vector. Using the project
        method projects the plane normal.

        Args:
            normal (array_like, optional):
                Vector representing the plane normal.
            pole (array_like, optional):
                Vector representing the plane pole (analagous to normal).
            strike (float, optional):
                Strike of the plane. Units may be specified, otherwise
                defaults to default unit system.
            dip (float, optional):
                Dip of the plane. Units may be specified, otherwise
                defaults to default unit system.
            dip_direction (float, optional):
                Dip direction of the plane. Units may be specified, otherwise
                defaults to default unit system.
            plunge (float, optional):
                Plunge of the plane. Units may be specified, otherwise
                defaults to default unit system.
            trend (float, optional):
                Trend of the plane. Units may be specified, otherwise
                defaults to default unit system.

        Returns:
            [type]: [description]
        """

        if normal is not None:
            vector = normal
        elif pole is not None:
            vector = pole
        elif strike is not None:
            vector = cls._normal_from_strike_and_dip(strike, dip)
        elif dip_direction is not None:
            vector = cls._normal_from_dip_and_direction(dip, dip_direction)
        elif dip is not None:
            vector = cls._normal_from_dip_and_direction(dip, dip_direction)
        else:
            vector = None

        return super().__new__(cls, vector=vector)

    @property
    def strike(self):
        """Strike of the orientation. Azimuth of the the intersection of the
        orientation with a horizontal plane.

        Returns:
            float:
                Strike of the orientation.
        """

        deg = units.Unit('deg')
        return (
            self.trend + 90 * deg if self.trend < 270 * deg else
            self.trend - 270 * deg
        )

    @strike.setter
    def strike(self, strike):
        """Sets the strike of the vector in place. The current dip of the
        vector is maintained.

        Args:
            strike (float):
                Strike of the orientation. krak.Units are supported, and
                will revert to default units in krak.settings if not specified.
        """

        self.values = self._normal_from_strike_and_dip(strike, self.dip)

    @property
    def dip(self):
        """Dip of the orientation. The steepest angle of descent of the
        orientation relative to a horizontal plane.

        Returns:
            float:
                Dip of the orientation.
        """

        return 90 * units.Unit('deg') - self.plunge

    @dip.setter
    def dip(self, dip):
        """Sets the dip of the vector in place. The current strike of the
        vector is maintained.

        Args:
            dip (float):
                Dip of the orientation. krak.Units are supported, and
                will revert to default units in krak.settings if not specified.
        """
        self.values = self._normal_from_strike_and_dip(self.strike, dip)

    @property
    def dip_direction(self):
        """Dip direction of the orientation. The azimuth of the direction of
        the dip as projected on a horizontal plane.

        Returns:
            float:
                Dip direction of the orientation.
        """

        deg = units.Unit('deg')
        return (
            self.trend + 180 * deg if self.trend < 180 * deg else
            self.trend - 180 * deg
        )

    @dip_direction.setter
    def dip_direction(self, dip_direction):
        """Sets the dip direction of the vector in place. The current strike of the
        vector is maintained.

        Args:
            dip_direction (float):
                Dip direction of the orientation. krak.Units are supported, and
                will revert to default units in krak.settings if not specified.
        """

        self.values = self._normal_from_dip_and_direction(
            self.dip, dip_direction)

    @property
    def normal(self):
        """Orientation normal. Alias for values attribute.

        Returns:
            np.ndarray:
                Underlying numpy array.
        """

        return Vector(self)

    @normal.setter
    def normal(self, normal):
        """Setter for underlying numpy array values

        Args:
            value (array-like):  array of length 2 or 3
        """

        self.values = normal

    @property
    def pole(self):
        """Orientation normal. Alias for values attribute.

        Returns:
            np.ndarray:
                Underlying numpy array.
        """

        return self.normal

    @pole.setter
    def pole(self, pole):
        """Setter for underlying numpy array values

        Args:
            value (array-like):  array of length 2 or 3
        """

        self.normal = pole

    @classmethod
    def _normal_from_strike_and_dip(cls, strike, dip):
        deg = units.Unit('deg')
        strike = (
            properties.Strike(strike).quantity if strike is not None else
            90 * deg)
        dip = (
            properties.Dip(dip).quantity if dip is not None else
            0 * deg)

        trend = strike - 90 * deg
        plunge = 90 * deg - dip

        trend = trend if trend > 0 else trend + 360 * deg
        return cls._vector_from_trend_and_plunge(trend, plunge)

    @classmethod
    def _normal_from_dip_and_direction(cls, dip, dip_direction):
        deg = units.Unit('deg')

        dip = (
            properties.Dip(dip).quantity if dip is not None else
            0 * deg)
        dip_direction = (
            properties.DipDirection(dip_direction).quantity
            if dip_direction is not None else 0 * deg)

        trend = dip_direction - 180 * deg
        plunge = 90 * deg - dip

        trend = trend if trend > 0 else trend + 360 * deg
        return cls._vector_from_trend_and_plunge(trend, plunge)

    def plot(self, origin=(0, 0, 0), scale=1.0, **kwargs):
        """Creates a visual representation (disc) of the orientation and plots
        it to the active canvas.

        Args:
            origin (array_like, optional):
                Position of the base of the vector representation.
                Defaults to (0, 0, 0).
            scale (float, optional):
                Size of the disc representation.
        """

        plotter = viewer.Window()
        size = (np.sqrt(self.magnitude) / np.pi) * scale
        disc = pv.Disc(
            center=np.array(origin), inner=0, outer=size,
            normal=self.values)
        plotter.add_mesh(disc, **kwargs)


class Line:
    """A Line object represents a vector with a positional reference

    """

    def __init__(self, *args, origin=None, **kwargs):
        """[summary]

        Args:
            origin ([type], optional): [description]. Defaults to None.
        """

        if origin is None:
            origin = (0, 0, 0)
        self.origin = Vector(origin)

        self.direction = Vector(*args, **kwargs)

    def __eq__(self, other):
        try:
            if self.origin != other.origin:
                return False
            if self.direction != other.direction:
                return False
        except AttributeError:
            raise TypeError(f'Cannot compare {self} with {other}')

        return True

    def __rshift__(self, other):
        return self.project(other)

    def project(self, destination):
        return Line(
            origin=self.origin >> destination,
            direction=self.direction >> destination,
        )

    def flip(self):
        return Line(origin=self.origin, direction=self.direction.flip())

    def plot(self, **kwargs):
        self.direction.plot(origin=self.origin, **kwargs)


class Plane:
    """[summary]
    """

    def __init__(self, *args, origin=None, orientation=None, **kwargs):
        self.origin = Vector(origin)
        if orientation is None:
            orientation = Orientation(*args, **kwargs)
        self.orientation = orientation

    def flip(self):
        return Plane(origin=self.origin, orientation=self.orientation.flip())

    def plot(self, **kwargs):
        self.direction.plot(origin=self.origin, **kwargs)
