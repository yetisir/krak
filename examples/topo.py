import krak
from krak import select

topo = krak.examples.random_hills().rotate(angle=33, axis=(1, 1, 0))
geology = krak.examples.random_hills()
# extrusion = topo.extrude_surface(distance=-40)
# model_boundary = extrusion.clip_closed(origin=(0, 0, -10)).remesh()
# mesh = model_boundary.tetrahedral_mesh()
# mesh.add_cell_group(
#     'monzonite',
#     range=select.Distance(mesh=geology, distance=2),
#     slot='geology')
# mesh.add_cell_group(
#     'sandstone',
#     range=select.PositionX(0, None),
#     slot='geology')
