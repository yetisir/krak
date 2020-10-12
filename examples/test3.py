import pandas as pd
import numpy as np
import pyvista as pv

##########
# Make a sample dataframe
df = pd.DataFrame()
df['x'] = np.array([0.0, 2.0])
df['y'] = np.array([0.0, 0.0])
df['z'] = np.array([0.0, 0.0])
df['x2'] = np.array([1.0, 2.0])
df['y2'] = np.array([0.0, 2.0])
df['z2'] = np.array([0.0, 0.0])
df['IDs'] = np.array(['Line ID 1', 'Line ID 2'])
##########

weaved = np.empty((len(df) * 2, 3))
weaved[0::2] = df[['x', 'y', 'z']].values
weaved[1::2] = df[['x2', 'y2', 'z2']].values


def lines_from_points(points):
    """Generates line from weaved points."""
    n_points = len(points)
    n_lines = n_points // 2
    lines = np.c_[(2 * np.ones(n_lines, np.int),
                   np.arange(0, n_points-1, step=2),
                   np.arange(1, n_points+1, step=2))]
    poly = pv.PolyData()
    poly.points = points
    poly.lines = lines
    return poly


lines = lines_from_points(weaved)
lines.cell_arrays['IDs'] = df['IDs'].values
lines.plot(line_width=5)
