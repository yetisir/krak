from abc import ABC, abstractmethod

import numpy as np
from scipy import optimize

from . import utils


class Base(ABC):
    def normal_stress(self, sigma_3, sigma_1=None, derivative=None):
        if sigma_1 is None:
            sigma_1 = self.sigma_1_strength(sigma_3)

        if derivative is None:
            derivative = self._envelope_derivative(sigma_3)

        return (
            ((sigma_1 + sigma_3) / 2.0) - ((sigma_1 - sigma_3) / 2.0) *
            ((derivative - 1) / (derivative + 1))
        )

    def shear_strength(self, sigma_3, sigma_1=None, derivative=None):
        if sigma_1 is None:
            sigma_1 = self.sigma_1_strength(sigma_3)

        if derivative is None:
            derivative = self._envelope_derivative(sigma_3)

        return (sigma_1 - sigma_3) * (np.sqrt(derivative) / (derivative + 1))

    @abstractmethod
    def sigma_1_strength(self, sig_3):
        raise NotImplementedError

    @abstractmethod
    def _envelope_derivative(self, sig_3):
        raise NotImplementedError


class MohrCoulomb(Base):
    def __init__(self, c, phi, sigma_t=None):

        self.c = utils.validate_positive(c, 'c')
        self.sigma_t = utils.validate_positive(sigma_t, 'sigma_t')
        self._phi = np.deg2rad(utils.validate_positive(phi, 'phi'))

        if self.sigma_t is None:
            self.sigma_t = -(self.c / np.tan(self._phi))

    @property
    def phi(self):
        return np.rad2deg(self._phi)

    def sigma_1_strength(self, sigma_3):
        return (
            (2 * self.c * np.cos(self._phi)) /
            (1-np.sin(self._phi)) +
            ((1 + np.sin(self._phi)) / (1 - np.sin(self._phi))) * sigma_3
        )

    def _envelope_derivative(self, sigma_3):
        return (1 + np.sin(self._phi)) / (1 - np.sin(self._phi))


class HoekBrown(Base):

    def __init__(
            self, sigma_ci, gsi=None, d=None, mi=None, mb=None, s=None,
            a=None, sigma_t=None):

        self.sigma_ci = utils.validate_positive(sigma_ci, 'sigma_ci')
        self.mi = utils.validate_positive(mi, 'mi')
        self.gsi = utils.validate_positive(gsi, 'gsi')
        self.d = utils.validate_positive(d, 'd')
        self.sigma_t = utils.validate_positive(sigma_t, 'sigma_t')

        mb = utils.validate_positive(mb, 'mb')
        s = utils.validate_positive(s, 's')
        a = utils.validate_positive(a, 'a')

        if self.mi is None:
            self.mb = mb

        if self.gsi is None:
            self.a = a if a is not None else 0.5

        if self.d is None:
            self.s = s if s is not None else 1.0

        if self.sigma_t is None:
            self.sigma_t = -(self.s * self.sigma_ci) / self.mb

    @property
    def mb(self):
        return self.mi * np.exp((self.gsi - 100.0)/(28.0 - (14.0 * self.d)))

    @mb.setter
    def mb(self, mb):
        self.mi = mb / np.exp((self.gsi - 100.0)/(28.0 - (14.0 * self.d)))

    @property
    def s(self):
        return np.exp((self.gsi - 100.0)/(9.0 - (3.0 * self.d)))

    @s.setter
    def s(self, s):
        self.d = (9.0 - (self.gsi - 100.0) / np.log(s)) * (1.0 / 3.0)

    @property
    def a(self):
        return (0.5 + (
            np.exp((np.negative(self.gsi)) / 15.0) -
            np.exp(-20.0 / 3.0)) / 6.0)

    @a.setter
    def a(self, a):
        self.gsi = -15.0 * np.log((a - 0.5) * 6 + np.exp(-20.0 / 3.0))

    @property
    def sigma_cm(self):
        numerator1 = (self.mb + 4 * self.s - self.a * (self.mb - 8 * self.s))
        numerator2 = np.power(self.mb / 4 + self.s, self.a - 1)
        denominator = 2 * (1 + self.a) * (2 + self.a)

        return self.sigma_ci * numerator1 * numerator2 / denominator

    def sigma_1_strength(self, sigma_3):
        base = (self.mb * (sigma_3 / self.sigma_ci) + self.s)
        if base < 0:
            return 0

        return sigma_3 + (self.sigma_ci * np.power(base, self.a))

    def _envelope_derivative(self, sigma_3):
        base = (self.mb * (sigma_3 / self.sigma_ci) + self.s)
        if base < 0:
            return 0
        return 1 + self.a * self.mb * np.power(base, self.a - 1)

    def equivalent_mc_average(
            self, sigma_3_max=None, H=None, gamma=None, excavation='slope'):

        if sigma_3_max is None:
            if excavation == 'slope':
                sigma_3_max = self._calculate_sigma_3_max(
                    H, gamma, 0.72, -0.91)
            elif excavation == 'tunnel':
                sigma_3_max = self._calculate_sigma_3_max(
                    H, gamma, 0.47, -0.94)

        phi = self._calculate_average_phi(sigma_3_max)
        c = self._calculate_average_c(sigma_3_max)

        return MohrCoulomb(c=c, phi=phi)

    def _calculate_sigma_3_max(self, H, gamma, coefficient, exponent):
        return coefficient * np.power(
            (self.sigma_cm / (H * gamma)), exponent) * self.sigma_cm

    def _calculate_average_phi(self, sigma_3_max):
        sigma_3_n = sigma_3_max / self.sigma_ci

        numerator = 6 * self.a * self.mb * np.power(
            self.s + self.mb * sigma_3_n, self.a - 1)
        denominator = 2 * (1 + self.a) * (2 + self.a) + numerator

        return np.rad2deg(np.arcsin(numerator / denominator))

    def _calculate_average_c(self, sigma_3_max):
        sigma_3_n = sigma_3_max / self.sigma_ci

        x1 = np.power(self.s + self.mb * sigma_3_n, self.a - 1)
        x2 = (1 + self.a) * (2 + self.a)
        numerator = (self.sigma_ci * (
            (1 + 2 * self.a) * self.s + (1 - self.a) *
            self.mb * sigma_3_n) * x1)
        denominator = x2 * np.sqrt(1 + 6 * self.a * self.mb * x1 / x2)

        return numerator / denominator

    def equivalent_mc_exact(
            self, sigma_3, sigma_1=None, correction_type='vertical'):

        if sigma_1 is None:
            sigma_1 = self.sigma_1_strength(sigma_3)

        if correction_type == 'vertical':
            sigma_3 = sigma_3

        elif correction_type == 'closest':
            sigma_3 = self._correct_closest(sigma_3, sigma_1)

        elif correction_type == 'hybrid':
            if sigma_1 > self.sigma_1_strength(sigma_3):
                sigma_3 = self._correct_closest(sigma_3, sigma_1)
            else:
                sigma_3 = sigma_3
        else:
            raise ValueError('invalid correction type specified')

        derivative = self._envelope_derivative(sigma_3)
        sigma_1 = self.sigma_1_strength(sigma_3)

        phi = np.rad2deg(
            np.arctan((derivative - 1) / (2 * np.sqrt(derivative))))
        c = (sigma_1 - (sigma_3 * derivative)) / (2 * np.sqrt(derivative))

        return MohrCoulomb(c=c, phi=phi)

    def _correct_closest(self, sigma_3, sigma_1):

        def test_closest(trial_sigma_3, sigma_3, sigma_1):
            trial_sigma_3 = trial_sigma_3[0]

            derivative = self._envelope_derivative(trial_sigma_3)
            trial_sig_1 = self.sigma_1_strength(trial_sigma_3)
            v1 = np.array([1, derivative])

            if trial_sig_1 > 0:
                v2 = np.array([sigma_3 - trial_sigma_3, sigma_1 - trial_sig_1])
            else:
                v2 = v1

            v1 = v1 / np.linalg.norm(v1)
            v2 = v2 / np.linalg.norm(v2)

            return abs(np.dot(v1, v2))

        closest_sigma_3 = optimize.fmin(test_closest, x0=sigma_3, args=(
            sigma_3, sigma_1), ftol=0.1, disp=False)
        return closest_sigma_3[0]
