from . import units

_si_units = units.SI()

gravitational_acceleration = (
    9.80665 * _si_units.acceleration
)
