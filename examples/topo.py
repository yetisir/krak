import pdb
import krak

topo = krak.examples.random_hills()

f = topo.extrude_surface(distance=10).remesh().tetrahedral_mesh()

f.plot()
