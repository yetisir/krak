"""Module containing mathematical and/or physical constants.

Constants defined in this module are returned as pint.Quantity
objects which contain the corresponding units. Quantities will
always be defined with SI units, but can be converted using
the .to() method.

Attributes:
    gravitational_acceleration (pint.Quantity):
        9.81 m/s^2
    constants.water_density (pint.Quantity):
        1000 kg/m^3
"""

from . import units

_units = units.MKS()

gravitational_acceleration = 9.81 * _units.acceleration
water_density = 1e3 * _units.density
