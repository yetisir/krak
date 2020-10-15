import matplotlib.pyplot as plt
import networkx as nx

graph = nx.DiGraph()
graph.add_edges_from([
    ('utils', 'config'),
    ('units', 'config'),
    ('constants', 'config'),
    ('mesh', 'connect'),
    ('units', 'constants'),
    ('spatial', 'filters'),
    ('strength', 'materials'),
    ('properties', 'materials'),
    ('filters', 'mesh'),
    ('viewer', 'mesh'),
    ('spatial', 'mesh'),
    ('metadata', 'mesh'),
    ('select', 'metadata'),
    ('utils', 'metadata'),
    ('units', 'metadata'),
    ('config', 'metadata'),
    ('materials', 'metadata'),
    ('units', 'properties'),
    ('config', 'properties'),
    ('select', 'spatial'),
    ('utils', 'strength'),
    ('spatial', 'strength'),
    ('properties', 'strength'),
    ('units', 'utils'),
    ('utils', 'viewer'),
])
nx.draw_kamada_kawai(graph, arrows=True, with_labels=True)

plt.show()
