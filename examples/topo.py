from pyvista import examples

import krak

topo = krak.load_mesh(examples.load_random_hills())

ext = krak.tools.extrude_topography(topo, -10)

