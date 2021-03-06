from . import utils, units, spatial, constants


class Settings(metaclass=utils.Singleton):
    def __init__(self):
        self._units = units.SI()
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
                raise ValueError(f'Unrecognized unit system name "{value}"')
        if not isinstance(value, units.UnitSystem):
            raise ValueError(f'Unrecognized unit system "{value}"')
        self._units = value

    @property
    def gravity_direction(self):
        return self._gravity.unit

    @gravity_direction.setter
    def gravity_direction(self, value):
        self._gravity = (
            spatial.Direction(value).scale(self.gravity_magnitude) *
            self.units.acceleration
        )

    @property
    def gravity_magnitude(self):
        return self._gravity.to(self.units.acceleration).magnitude.magnitude

    @gravity_magnitude.setter
    def gravity_magnitude(self, value):
        value = utils.parse_quantity(
            value, default_units=self.units.acceleration)
        self._gravity = self._gravity.magnitude.scale(
            value.magnitude) * value.units

    @property
    def gravity(self):
        return self._gravity

    @gravity.setter
    def gravity(self, value):
        value = utils.parse_quantity(
            value, default_units=self.units.acceleration)
        self._gravity = spatial.Direction(value.magnitude) * value.units

    @property
    def water_density(self):
        return self._water_density

    @water_density.setter
    def water_density(self, value):
        self._water_density = utils.parse_quantity(value, self.units.density)


settings = Settings()
