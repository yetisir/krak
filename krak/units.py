import pint
import pint_pandas

registry = pint.UnitRegistry()
pint_pandas.PintType.ureg = registry


class Dimension(pint.util.UnitsContainer):

    def __init__(self, length=None, mass=None, time=None):
        args = {}
        if length:
            args['[length]'] = length
        if mass:
            args['[mass]'] = mass
        if time:
            args['[time]'] = time

        super().__init__(**args)


class Dimensionless(Dimension):
    def __init__(self):
        super().__init__()


class Angle(Dimension):
    def __init__(self):
        super().__init__()


class Length(Dimension):
    def __init__(self):
        super().__init__(length=1)


class Mass(Dimension):
    def __init__(self):
        super().__init__(mass=1)


class Time(Dimension):
    def __init__(self):
        super().__init__(time=1)


class Force(Dimension):
    def __init__(self):
        super().__init__(length=1, mass=1, time=-2)


class Pressure(Dimension):
    def __init__(self):
        super().__init__(length=-1, mass=1, time=-2)


class Velocity(Dimension):
    def __init__(self):
        super().__init__(length=1, time=-1)


class Acceleration(Dimension):
    def __init__(self):
        super().__init__(length=1, time=-2)


class Density(Dimension):
    def __init__(self):
        super().__init__(length=-3, mass=1)


class Energy(Dimension):
    def __init__(self):
        super().__init__(length=2, mass=1, time=-2)


class Power(Dimension):
    def __init__(self):
        super().__init__(length=2, mass=1, time=-3)


class Unit(registry.Unit):
    pass


class Quantity(registry.Quantity):
    pass


class UnitSystem:
    def __init__(
            self, length, mass, time, angle, force=None, pressure=None,
            velocity=None, acceleration=None, density=None, energy=None,
            power=None):
        self.length = length
        self.mass = mass
        self.time = time
        self.angle = angle

        self.force = force
        self.pressure = pressure
        self.velocity = velocity
        self.acceleration = acceleration
        self.density = density
        self.energy = energy
        self.power = power

    @property
    def dimensionality_map(self):
        return {
            Dimensionless(): Unit(''),
            Force(): self.force,
            Pressure(): self.pressure,
            Velocity(): self.velocity,
            Acceleration(): self.acceleration,
            Density(): self.density,
            Energy(): self.energy,
            Power(): self.power,
        }

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, value):
        self._length = self._validate_unit(value, Length())

    @property
    def mass(self):
        return self._mass

    @mass.setter
    def mass(self, value):
        self._mass = self._validate_unit(value, Mass())

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, value):
        self._time = self._validate_unit(value, Time())

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = self._validate_unit(value, Angle())

    @property
    def force(self):
        return self._force or self.mass * self.acceleration

    @force.setter
    def force(self, value):
        self._force = self._validate_unit(value, Force())

    @property
    def pressure(self):
        return self._pressure or self.force / (self.length ** 2)

    @pressure.setter
    def pressure(self, value):
        self._pressure = self._validate_unit(value, Pressure())

    @property
    def velocity(self):
        return self._velocity or self.length / self.time

    @velocity.setter
    def velocity(self, value):
        self._velocity = self._validate_unit(value, Velocity())

    @property
    def acceleration(self):
        return self._acceleration or self.velocity / self.time

    @acceleration.setter
    def acceleration(self, value):
        self._acceleration = self._validate_unit(value, Acceleration())

    @property
    def density(self):
        return self._density or self.mass / (self.length ** 3)

    @density.setter
    def density(self, value):
        self._density = self._validate_unit(value, Density())

    @property
    def energy(self):
        return self._energy or self.force * self.length

    @energy.setter
    def energy(self, value):
        self._energy = self._validate_unit(value, Energy())

    @property
    def power(self):
        return self._power or self.energy / self.time

    @power.setter
    def power(self, value):
        self._power = self._validate_unit(value, Power())

    def convert(self, quantity):
        if quantity.dimensionless:
            return quantity

        if not isinstance(quantity, registry.Quantity):
            raise TypeError(f'Unrecognized quantity "{quantity}"')

        units = self.dimensionality_map.get(
            quantity.dimensionality) or self._get_base_units(quantity.units)

        return quantity.to(units)

    def _get_base_units(self, units):
        base_units = Unit('')
        for dimension, order in units.dimensionality.items():
            base_units = base_units * (getattr(self, dimension[1:-1]) ** order)
        return base_units

    def _validate_unit(self, unit, dimensionality):
        if unit is None:
            return unit

        if isinstance(unit, str):
            try:
                unit = Unit(unit)
            except pint.errors.UndefinedUnitError:
                raise ValueError(f'Unrecognized unit {unit}')
        if not isinstance(unit, Unit):
            raise TypeError(f'Unrecognized unit type {unit}')

        if unit.dimensionality != dimensionality:
            raise ValueError(
                f'Incorrect unit dimensionality "{unit.dimensionality}" '
                f'for unit "{unit}"')

        return unit


class SI(UnitSystem):
    def __init__(
            self,
            length='meter',
            mass='kilogram',
            time='second',
            angle='degree',
            pressure='pascal',
            force='newton',
            energy='joule',
            power='watt',
            **kwargs):
        super().__init__(
            length=length,
            mass=mass,
            time=time,
            angle=angle,
            pressure=pressure,
            force=force,
            energy=energy,
            power=power,
            **kwargs
        )


class MKS(UnitSystem):
    def __init__(
            self,
            length='meter',
            mass='kilogram',
            time='second',
            angle='degree',
            **kwargs):
        super().__init__(
            length=length,
            mass=mass,
            time=time,
            angle=angle,
            **kwargs,
        )


class CGS(UnitSystem):
    def __init__(
            self,
            length='centimeter',
            mass='gram',
            time='second',
            angle='degree',
            **kwargs):
        super().__init__(
            length=length,
            mass=mass,
            time=time,
            angle=angle,
            **kwargs,
        )


class US(UnitSystem):
    def __init__(
            self,
            length='foot',
            mass='slug',
            time='second',
            angle='degree',
            force='force_pound',
            **kwargs):
        super().__init__(
            length=length,
            mass=mass,
            time=time,
            angle=angle,
            force=force,
            **kwargs
        )
