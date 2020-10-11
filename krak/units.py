import pint

units = pint.UnitRegistry()


class UnitSystem:
    def __init__(self, length, mass, time):
        self.length = self._validate_unit(length, 'length')
        self.mass = self._validate_unit(mass, 'mass')
        self.time = self._validate_unit(time, 'time')

    @property
    def force(self):
        return self.mass * self.acceleration

    @property
    def pressure(self):
        return self.force / (self.length ** 2)

    @property
    def velocity(self):
        return self.length / self.time

    @property
    def acceleration(self):
        return self.velocity / self.time

    @property
    def density(self):
        return self.mass / (self.length ** 3)

    @property
    def energy(self):
        return self.force * self.length

    @property
    def power(self):
        return self.energy / self.time

    def _validate_unit(self, unit, type):
        if isinstance(unit, str):
            try:
                unit = getattr(units, unit)
            except pint.errors.UndefinedUnitError:
                raise ValueError(f'Unrecognized unit {unit}')

        dimensionality = pint.util.UnitsContainer({f'[{type}]': 1})
        if unit.dimensionality != dimensionality:
            raise ValueError(
                f'Incorrect unit dimensionality {unit.dimensionality}'
                f' for unit {unit}')

        return unit


class MKS(UnitSystem):
    def __init__(self):
        super().__init__(
            length=units.meter,
            mass=units.kilogram,
            time=units.second,
        )


class US(UnitSystem):
    def __init__(self):
        super().__init__(
            length=units.foot,
            mass=units.slug,
            time=units.second,
        )


class CGS(UnitSystem):
    def __init__(self):
        super().__init__(
            length=units.centimeter,
            mass=units.gram,
            time=units.second,
        )


class SI(MKS):
    pass


def parse(unit):
    try:
        return pint.Unit(unit)
    except pint.errors.UndefinedUnitError:
        raise ValueError(f'Unit "{unit}" not recognized')
