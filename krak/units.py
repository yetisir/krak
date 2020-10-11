import pint


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

    def convert(self, quantity):
        if not isinstance(quantity, pint.Quantity):
            raise TypeError(f'Unrecognized quantity "{quantity}"')

        return quantity.to(self._get_base_units(quantity.units))

    def _get_base_units(self, units):
        base_units = pint.Unit('')
        for dimension, order in units.dimensionality.items():
            base_units = base_units * (getattr(self, dimension[1:-1]) ** order)
        return base_units

    def _validate_unit(self, unit, type):
        if isinstance(unit, str):
            try:
                unit = pint.Unit(unit)
            except pint.errors.UndefinedUnitError:
                raise ValueError(f'Unrecognized unit {unit}')
        if not isinstance(unit, pint.Unit):
            raise TypeError(f'Unrecognized unit type {unit}')

        dimensionality = pint.util.UnitsContainer({f'[{type}]': 1})
        if unit.dimensionality != dimensionality:
            raise ValueError(
                f'Incorrect unit dimensionality "{unit.dimensionality}" '
                f'for unit "{unit}"')

        return unit


class SI(UnitSystem):
    def __init__(self):
        super().__init__(
            length='meter',
            mass='kilogram',
            time='second',
        )


class MKS(UnitSystem):
    def __init__(self):
        super().__init__(
            length='meter',
            mass='kilogram',
            time='second',
        )


class CGS(UnitSystem):
    def __init__(self):
        super().__init__(
            length='centimeter',
            mass='gram',
            time='second',
        )


class US(UnitSystem):
    def __init__(self):
        super().__init__(
            length='foot',
            mass='slug',
            time='second',
        )


def parse(unit):
    try:
        return pint.Unit(unit)
    except pint.errors.UndefinedUnitError:
        raise ValueError(f'Unit "{unit}" not recognized')
