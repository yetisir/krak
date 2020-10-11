from . import units

_si_units = units.SI()

gravitational_acceleration = 9.81 * _si_units.acceleration
water_density = 1e3 * _si_units.density
