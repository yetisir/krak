import krak

topo = krak.examples.random_hills()

extrusion = topo.extrude_surface(distance=-20).remesh()

boundary = extrusion.clip_closed(origin=(0, 0, -10)).remesh()


f = boundary.tetrahedral_mesh()

f.plot()
