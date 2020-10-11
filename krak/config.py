import pint

from . import utils, units, spatial, constants, unit_systems


class Settings(metaclass=utils.Singleton):
    def __init__(self):
        self._units = unit_systems.SI()
        self._gravity = spatial.Direction(
            [0, 0, -1]) * constants.gravitational_acceleration
        self._water_density = constants.water_density

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
            assert self.units.acceleration.dimensionality == value.units.dimensionality
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
        value, units = self._validate_units(value, 'acceleration')
        self._gravity = spatial.Direction(value) * units

    @property
    def water_density(self):
        return self.water_density

    @water_density.setter
    def water_density(self, value):
        value, units = self._validate_units(value, 'density')
        self._water_density = value * units

    def _validate_units(self, value, type):
        reference_units = getattr(self.units, type)

        if isinstance(value, pint.Quantity):
            assert reference_units.dimensionality == value.units.dimensionality
            units = value.units
            value = value.magnitude
        else:
            units = reference_units

        return units, value
