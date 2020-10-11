from . import units, settings


class Property():
    def __init__(self, value, units):
        pass


class Density(Property):
    def __init__(self, value, units=None):
        if units is None:
            units = settings.units.density
        else:
            assert settings.units.density.dimensionality == units.dimensionality
        super().__init__(units)


class ShearModulus(Property):
    pass


class BulkModulus(Property):
    pass


class PoissonsRatio(Property):
    pass


class YoungsModulus(Property):
    pass


class FrictionAngle(Property):
    pass


class DilationAngle(Property):
    pass


class CohesiveStrength(Property):
    pass


class TensileStrength(Property):
    pass
