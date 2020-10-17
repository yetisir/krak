import numbers

import pandas as pd
import numpy as np
import pint_pandas

from . import units, config


class Property:
    dimensions = units.Dimensionless()
    name = ''
    min_value = float('-inf')
    max_value = float('inf')
    allowed_units = None

    def __init__(self, value):
        if isinstance(value, Property):
            value = value.value

        if isinstance(value, pd.Series):
            value = value.values

        if isinstance(value, pint_pandas.pint_array.PintArray):
            value = units.Quantity(value.data, value.units)

        quantity = self._parse_quantity(value)
        self.check_value(quantity)

        self.quantity = quantity

    def default_unit(self):
        return config.settings.units.dimensionality_map[self.dimensions]

    def check_value(self, value):
        min_value = self._parse_quantity(self.min_value)
        max_value = self._parse_quantity(self.max_value)

        condition = (value < min_value) | (value > max_value)
        if not isinstance(condition, bool):
            condition = condition.any()
        if condition:
            raise ValueError(
                f'{self.name} must be between {self.min_value} '
                f'and {self.max_value}')

    def _parse_quantity(self, value, unit=None):
        if isinstance(value, units.registry.Quantity):
            unit = value.units
            value = value.magnitude
        else:
            unit = unit or self.default_unit()

        if self.dimensions != unit.dimensionality:
            raise ValueError(
                f'Incompatible unit "{unit}" for property "{self.name}"')
        if not isinstance(value, numbers.Number):
            value = np.array(value)
            if not np.issubdtype(value.dtype, np.number):
                raise ValueError(
                    f'Property "{self.name}" value must be numeric')

        if self.allowed_units is not None:
            if unit not in self.allowed_units:
                raise ValueError(f'Unit {unit} not a {self.name} unit')

        return value * unit


class Density(Property):
    dimensions = units.Density()
    name = 'density'
    min_value = 0
    max_value = float('inf')


class ShearModulus(Property):
    dimensions = units.Pressure()
    name = 'shear'
    min_value = 0
    max_value = float('inf')


class BulkModulus(Property):
    dimensions = units.Pressure()
    name = 'bulk'
    min_value = 0
    max_value = float('inf')


class PoissonsRatio(Property):
    dimensions = units.Dimensionless()
    name = 'poisson'
    min_value = -1
    max_value = 0.5
    allowed_units = [
        units.Unit('')
    ]


class YoungsModulus(Property):
    dimensions = units.Pressure()
    name = 'young'
    min_value = 0
    max_value = float('inf')


class AngleProperty(Property):
    dimensions = units.Angle()
    allowed_units = [
        units.Unit('degree'), units.Unit('radians')
    ]

    def default_unit(self):
        return config.settings.units.angle


class FrictionAngle(AngleProperty):
    name = 'friction'
    min_value = 0
    max_value = 90 * units.Unit('degree')


class DilationAngle(AngleProperty):
    name = 'dilation'
    min_value = 0
    max_value = 90 * units.Unit('degree')


class CohesiveStrength(Property):
    dimensions = units.Pressure()
    name = 'cohesion'
    min_value = 0
    max_value = float('inf')


class TensileStrength(Property):
    dimensions = units.Pressure()
    name = 'tension'
    min_value = 0
    max_value = float('inf')


# Spatial Properties - move elsewhere?
class Trend(AngleProperty):
    name = 'trend'
    min_value = 0
    max_value = 360 * units.Unit('degree')


class Plunge(AngleProperty):
    name = 'plunge'
    min_value = -90 * units.Unit('degree')
    max_value = 90 * units.Unit('degree')


class Strike(AngleProperty):
    name = 'strike'
    min_value = 0 * units.Unit('degree')
    max_value = 360 * units.Unit('degree')


class Dip(AngleProperty):
    name = 'dip'
    min_value = 0 * units.Unit('degree')
    max_value = 90 * units.Unit('degree')


class DipDirection(AngleProperty):
    name = 'dip_direction'
    min_value = 0 * units.Unit('degree')
    max_value = 360 * units.Unit('degree')
