import numpy as np

from krak import spatial

# Setup functions


def reference_vector_3D():
    return [1.2, 2.3, 3.4]


def reference_vector_2D():
    return [1.2, 2.3]


def vector_3D():
    return spatial.Vector(reference_vector_3D())


def vector_2D():
    return spatial.Vector(reference_vector_2D())

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


def test_vector_values_setter():
    vector = vector_3D()
    vector.values = [4.5, 5.6, 6.7]
    assert vector == spatial.Vector([4.5, 5.6, 6.7])


def test_vector_magnitude_property():
    assert np.isclose(vector_3D().magnitude, 4.27668095606862)


def test_vector_magnitude_setter():
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


def test_vector_xyz_setters():
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
