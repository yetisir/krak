from pyvista import examples

import krak

topo = krak.load_mesh(examples.load_random_hills())
cow = krak.load_mesh('cow.obj')

t = topo.extrude([0, 0, -10])
# cow.clip_closed(normal=(0, 1, 1), origin=(0, 0, 0))

ext = krak.tools.extrude_topography(topo, -1)

