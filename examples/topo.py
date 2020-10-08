import krak
from krak import select, materials

# krak.set_default_units(krak.units.SI())

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
    property=property.ShearModulus(1.5e6),
    range=select.All())

model = krak.model(mesh=mesh)
