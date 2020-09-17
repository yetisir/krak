import krak
from krak import select

topo = krak.examples.random_hills()

rotated = topo.rotate(angle=33, axis=(1, 1, 0))

rotated.add_point_group('left', range=select.PositionX('min', 0))
rotated.add_point_group('right', range=select.PositionX(0, 'max'))

extrusion = topo.extrude_surface(distance=-20).remesh()

boundary = extrusion.clip_closed(origin=(0, 0, -10)).remesh()


f = boundary.tetrahedral_mesh()

f.plot()
