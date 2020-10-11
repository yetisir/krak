import krak
from krak import select, materials

# krak.set_default_units(krak.units.SI())

# krak.settings.gravity_magnitude = 9.8 * krak.parse_units('m/s^2')

topo = krak.examples.random_hills().rotate(angle=33, axis=(1, 1, 0))
extrusion = topo.extrude_surface(distance=-40)
clipped = extrusion.clip(origin=(0, 0, -10), closed=True)
mesh = clipped.voxel_mesh()

geology = krak.examples.random_hills().expand(10)
mesh.set_cell_group(
    group='limestone',
    slot='geology',
    range=select.All(),
)

mesh.set_cell_group(
    group=krak.Group(name='limestone', slot=geology)
    range=select.All()
)

cell_group = mesh.get_cell_group(name, slot)

mesh.cell_groups.add(krak.group(name))

mesh.cell_groups['geology', select.All()] = 'monzonite'
mesh.cell_groups['geology', select.Bottom()] = 'limestone'
mesh.cell_groups['lithology', select.Group(
    'monzonite', slot='geology')] = 'monzonite'


mesh.properties['shear', select.All()] = 1e-6

mesh.cell_fields['elevation', select.Top()] = 1e-6


mesh.set_cell_group(
    group='monzonite',
    slot='geology',
    range=select.Distance(mesh=geology, distance=10),
)
mesh.set_cell_field(
    name='elevation',
    values=1.0,
    range=select.All()
)

monzonite = materials.MohrCoulomb(
    density=10, bulk=3e6, shear=1e6,
    friction_angle=30, dilation_angle=10, cohesion=1e4)
limestone = materials.MohrCoulomb(
    density=15, bulk=5e6, shear=2e6,
    friction_angle=35, dilation_angle=15, cohesion=2e4)

mesh.set_material(
    material=limestone, range=select.Group(group='limestone', slot='geology'))
mesh.set_material(
    material=monzonite, range=select.Group(group='monzonite', slot='geology'))

mesh.set_property(
    property=krak.ShearModulus(1e6), range=select.All()
)

mesh.set_property(
    property='shear_modulus', range=select.All()
)

mesh.set_property(
    property=property.ShearModulus(1.5e6),
    range=select.All())

model = krak.model(mesh=mesh)
