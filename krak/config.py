import pint

from . import utils, units, spatial, constants


class Settings(metaclass=utils.Singleton):
    def __init__(self):
        self._units = units.SI()
        self._gravity = spatial.Direction(
            [0, 0, -1]) * constants.gravitational_acceleration

    @property
    def units(self):
        return self._units

    @units.setter
    def units(self, value):
        if isinstance(value, str):
            try:
                value = getattr(units, value)()
            except AttributeError:
                raise ValueError('Unrecognized unit system name "{value}"')
        if not isinstance(value, units.UnitSystem):
            raise ValueError('Unrecognized unit system "{value}"')
        self._units = value

    @property
    def gravity_direction(self):
        return self._gravity.unit

    @gravity_direction.setter
    def gravity_direction(self, value):
        import pdb
        pdb.set_trace()
        self._gravity = (
            spatial.Direction(value).scale(self.gravity_magnitude) *
            self.units.acceleration
        )

    @property
    def gravity_magnitude(self):
        return self._gravity.to(self.units.acceleration).magnitude.magnitude

    @gravity_magnitude.setter
    def gravity_magnitude(self, value):
        if isinstance(value, pint.Quantity):
            units = value.units
            value = value.magnitude
        else:
            units = self.units.acceleration

        self._gravity = self._gravity.magnitude.scale(value) * units

    @property
    def gravity(self):
        return self._gravity

    @gravity.setter
    def gravity(self, value):
        if isinstance(value, pint.Quantity):
            units = value.units
            value = value.magnitude
        else:
            units = self.units.acceleration

        self._gravity = spatial.Direction(value) * units
