import krak
from krak import select  # , materials

# krak.set_default_units(krak.units.SI())

# krak.settings.gravity_magnitude = 9.8 * krak.parse_units('m/s^2')

topo = krak.examples.random_hills().rotate(angle=33, axis=(1, 1, 0))
extrusion = topo.extrude_surface(distance=-40)
clipped = extrusion.clip(origin=(0, 0, -10), closed=True)
mesh = clipped.voxel_mesh()

geology = krak.examples.random_hills().expand(10)
mesh.cell_sets['geology', select.All()] = 'limestone'
mesh.cell_sets['geology', select.Distance(geology, 5)] = 'monzonite'

mesh.properties['model'] = 'mohr-coulomb'

# limestone = materials.Elastic(density=10, shear=1e6, bulk=2e6)

# limestone.apply(mesh, range=select.All())
# mesh.add_material(limestone, range=select.All())
# mesh.add_


# mesh.properties['shear', select.All()] = 1e-6 * krak.unit('MPa')
# mesh.cell_fields['elevation'] = 10 * krak.unit('m')
# mesh.cell_fields['elevation'] = 10 * krak.unit('m/s')

# mesh.cell_fields['elevation', select.Top()] = 1e-6


# mesh.set_cell_group(
#     group='monzonite',
#     slot='geology',
#     range=select.Distance(mesh=geology, distance=10),
# )
# mesh.set_cell_field(
#     name='elevation',
#     values=1.0,
#     range=select.All()
# )

# monzonite = materials.MohrCoulomb(
#     density=10, bulk=3e6, shear=1e6,
#     friction_angle=30, dilation_angle=10, cohesion=1e4)
# limestone = materials.MohrCoulomb(
#     density=15, bulk=5e6, shear=2e6,
#     friction_angle=35, dilation_angle=15, cohesion=2e4)
# mesh.set_property(
#     property=krak.ShearModulus(1e6), range=select.All()
# )

# mesh.set_property(
#     property='shear_modulus', range=select.All()
# )

# mesh.set_property(
#     property=property.ShearModulus(1.5e6),
#     range=select.All())

# model = krak.model(mesh=mesh)
