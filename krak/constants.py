from . import unit_systems

_si_units = unit_systems.SI()

gravitational_acceleration = 9.81 * _si_units.acceleration
water_density = 1e3 * _si_units.density
