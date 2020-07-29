import pdb
import krak

topo = krak.examples.random_hills()

extrusion = topo.extrude_surface(distance=-20).remesh()

pdb.set_trace()

boundary = extrusion.clip(origin=(0, 0, -10), flip=True).remesh()


f = boundary.tetrahedral_mesh()

f.plot()
