import numpy as np

from krak import spatial, units

# Setup functions


def reference_vector_3D():
    return [1.2, 2.3, 3.4]


def reference_vector_2D():
    return [1.2, 2.3]


def vector_3D():
    return spatial.Vector(reference_vector_3D())


def vector_2D():
    return spatial.Vector(reference_vector_2D())


def degrees():
    return units.Unit('degrees')


# Test functions


def test_vector_construction_default():
    assert spatial.Vector() == spatial.Vector([0, 0, 1])


def test_vector_construction_list():
    assert vector_3D() == spatial.Vector(reference_vector_3D())


def test_vector_construction_numpy():
    assert vector_3D() == spatial.Vector(np.array(reference_vector_3D()))


def test_vector_construction_krak():
    assert vector_3D() == spatial.Vector(vector_3D())


def test_vector_scalar_product_right():
    assert vector_3D() * 5.4 == spatial.Vector(
        [i * 5.4 for i in reference_vector_3D()])


def test_vector_scalar_product_left():
    assert 5.4 * vector_3D() == spatial.Vector(
        [i * 5.4 for i in reference_vector_3D()])


def test_vector_dot_product():
    assert vector_3D() * vector_3D() == 18.29


def test_vector_cross_product():
    assert vector_3D() ** vector_3D() == spatial.Vector([0, 0, 0])


def test_vector_values_property():
    assert (vector_3D().values == np.array(reference_vector_3D())).all()

    vector = vector_3D()
    vector.values = [4.5, 5.6, 6.7]
    assert vector == spatial.Vector([4.5, 5.6, 6.7])


def test_vector_magnitude_property():
    assert np.isclose(vector_3D().magnitude, 4.27668095606862)

    vector = vector_3D()
    vector.magnitude = 6.5
    assert np.isclose(vector, spatial.Vector(
        [1.82384426, 3.49570149, 5.16755873])).all()


def test_vector_equivalence():
    assert vector_3D() == spatial.Vector(reference_vector_3D())
    assert vector_3D() != vector_3D() * 2
    assert vector_3D() != -vector_3D()


def test_vector_xyz_properties():
    assert vector_3D().x == 1.2
    assert vector_3D().y == 2.3
    assert vector_3D().z == 3.4

    vector = vector_3D()
    vector.x = 4.5
    vector.y = 5.6
    vector.z = 6.7

    assert vector == spatial.Vector([4.5, 5.6, 6.7])


def test_vector_projection():
    vector = vector_3D()

    assert vector.project(vector) == vector
    assert vector.project([5.6, 6.7, 7.8]) == spatial.Vector(
        [1.98730761, 2.3776716, 2.7680356])


def test_vector_trend_property():
    vector = vector_3D()
    vector.trend = 50
    assert np.isclose(vector.trend, 50 * degrees())
    vector.trend = 120
    assert np.isclose(vector.trend, 120 * degrees())
    vector.trend = 220
    assert np.isclose(vector.trend, 220 * degrees())
    vector.trend = 305
    assert np.isclose(vector.trend, 305 * degrees())


def test_vector_plunge_property():
    vector = vector_3D()
    vector.plunge = 90
    assert np.isclose(vector.plunge, 90 * degrees())


def test_orientation_construction_default():
    assert spatial.Orientation() == spatial.Orientation([0, 0, 1])


def test_orientation_construction_normal():
    assert spatial.Orientation(normal=reference_vector_3D()) == vector_3D()
    assert spatial.Orientation(normal=vector_3D()) == vector_3D()


def test_orientation_construction_pole():
    assert spatial.Orientation(pole=reference_vector_3D()) == vector_3D()
    assert spatial.Orientation(pole=vector_3D()) == vector_3D()


def test_orientation_construction_strike_and_dip():
    orientation = spatial.Orientation(strike=120, dip=30)
    assert orientation == spatial.Orientation(
        [0.25, 0.4330127, -0.8660254])


def test_orientation_construction_dip_and_dip_drection():
    orientation = spatial.Orientation(dip=34, dip_direction=55)
    assert orientation == spatial.Orientation(
        [-0.45806401, -0.32073987, -0.82903757])


def test_orientation_strike_property():
    orientation = spatial.Orientation(strike=120, dip=30)
    assert np.isclose(orientation.strike, 120 * degrees())

    orientation.strike = 55
    assert np.isclose(orientation.strike, 55 * degrees())


def test_orientation_dip_property():
    orientation = spatial.Orientation(strike=120, dip=30)
    assert np.isclose(orientation.dip, 30 * degrees())

    orientation = spatial.Orientation(dip=34, dip_direction=55)
    assert np.isclose(orientation.dip, 34 * degrees())

    orientation.dip = 55
    assert np.isclose(orientation.dip, 55 * degrees())


def test_orientation_dip_direction_property():
    orientation = spatial.Orientation(dip=34, dip_direction=55)
    assert np.isclose(orientation.dip_direction, 55 * degrees())

    orientation.dip_direction = 310
    assert np.isclose(orientation.dip_direction, 310 * degrees())


def test_orientation_normal_property():
    orientation = spatial.Orientation(dip=34, dip_direction=55)

    orientation.normal = reference_vector_3D()
    assert orientation.normal == vector_3D()


def test_orientation_pole_property():
    orientation = spatial.Orientation(dip=34, dip_direction=55)

    orientation.pole = reference_vector_3D()
    assert orientation.pole == vector_3D()


def test_orientation_projection():
    vector = vector_3D()

    assert vector.project(vector) == vector
    assert (
        vector.project(spatial.Orientation([5.6, 6.7, 7.8])) ==
        spatial.Vector([-0.78730761, -0.0776716,  0.6319644])
    )


def test_line_constructor():
    line = spatial.Line(reference_vector_3D(), origin=reference_vector_3D())

    assert line.direction == vector_3D()
    assert line.origin == vector_3D()


def test_line_projection():
    line = spatial.Line(reference_vector_3D(), origin=reference_vector_3D())

    projection = line.project([5.6, 6.7, 7.8])

    assert isinstance(projection, spatial.Line)
    assert projection.direction == spatial.Vector(
        (1.98730761, 2.3776716, 2.7680356))
    assert projection.origin == spatial.Vector(
        (1.98730761, 2.3776716, 2.7680356))
    assert line.project(reference_vector_3D()) == line


def test_line_flip():
    line = spatial.Line(reference_vector_3D(), origin=reference_vector_3D())
    flipped = line.flip()
    assert flipped.direction == vector_3D().flip()
    assert flipped.origin == vector_3D()
