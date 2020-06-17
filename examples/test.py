import meshio
import meshzoo
import optimesh
import numpy as np
from pyvista import examples
import pyvista
from meshpy.triangle
import krak


points, cells = meshzoo.tetra_sphere(20)
mesh = krak.load_mesh(examples.load_random_hills())
points = mesh.points.values
cells = mesh.cells.values




class Sphere:
    def f(self, x):
       ff = pyvista.PolyData(x).sample(mesh.pv_mesh.elevation())
       import pdb; pdb.set_trace()

    def grad(self, x):
        return -2 * x

# You can use all methods in optimesh:
# points, cells = optimesh.cpt.fixed_point_uniform(
# points, cells = optimesh.odt.fixed_point_uniform(
points, cells = optimesh.cvt.quasi_newton_uniform_full(
    points, cells, 1.0e-2, 100, verbose=False,
    implicit_surface=Sphere(),
    # step_filename_format="out{:03d}.vtk"
)

m_cells = [('triangle', np.array([cell])) for cell in cells]

mesh = meshio.Mesh(points, m_cells)
mesh.write('test.obj')

import krak
k_mesh = krak.load_mesh(mesh).plot()
