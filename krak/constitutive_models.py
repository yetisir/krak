from abc import ABC, abstractmethod

from . import strength_models, utils


class Base(ABC):
    def __init__(self, density):
        self.density = density

    @property
    @abstractmethod
    def name(self):
        raise NotImplementedError


class Null(Base):
    name = 'null'


class Elastic():
    name = 'elastic'

    def __init__(self, bulk=None, shear=None, poisson=None, young=None):
        self.shear = None
        self.bulk = None

        self.set_elastic_parameters(
            bulk=bulk, shear=shear, poisson=poisson, young=young)

    @property
    def poisson(self):
        return (3 * self.bulk - 2 * self.shear) / (2 * (3 * self.bulk + self.shear))

    @property
    def young(self):
        return (9 * self.shear * self.bulk) / (3 * self.bulk + self.shear)

    def set_elastic_parameters(self, bulk=None, shear=None, poisson=None, young=None):
        self.shear = utils.validate_positive(shear, 'shear')
        self.bulk = utils.validate_positive(bulk, 'bulk')

        poisson = utils.validate_positive(bulk, 'poisson')
        young = utils.validate_positive(bulk, 'young')

        if shear is None:
            shear = young / (2.0 * (1.0 + poisson))
        if bulk is None:
            bulk = young / (3.0 * (1.0 - 2 * poisson))


class MohrCoulomb(strength_models.MohrCoulomb, Elastic):
    name = 'mohr-coulomb'

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)


class HoekBrown(strength_models.HoekBrown, Elastic):
    name = 'hoek-brown'

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
