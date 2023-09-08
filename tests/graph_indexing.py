import igraph as ig
import time
g = ig.Graph()
g.add_vertices(5)
g.add_edges([(0,2), (2,4), (1,3)], attributes={'name': [(0,2), (4,2), (1,3)]})

#g.vs[1]['name'] = 1
g.add_vertices('A')

g = ig.Graph.Barabasi(n=10000)
g.vs['name'] = [v.index for v in g.vs]

target = list(range(10000))

tm = time.time()
idx = [g.vs.find(name=v).index for v in target]
g.vs.select(idx)
print(time.time()-tm)

tm = time.time()
g.vs.select(target)
print(time.time()-tm)