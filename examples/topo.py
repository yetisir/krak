import krak
from krak import select

topo = krak.examples.random_hills()  # .rotate(angle=33, axis=(1, 1, 0))
topo = topo.extend((11, 0, 0), snap_to_axis=False)
topo = topo.extend((-11, 0, 0), snap_to_axis=False)
topo = topo.extend((0, 11, 0), snap_to_axis=False)
topo = topo.extend((0, -11, 0), snap_to_axis=False)
extrusion = topo.extrude_surface(distance=-40)
clipped = extrusion.clip(closed=True)
