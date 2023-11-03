import matplotlib.pyplot as plt
import matplotlib.animation as animation
import igraph as ig


def animate(fig, ax, graph, vertex_colors, graph_layout,
            frames, save_as, interval=500, blit=True, fps=60,
            writer='pillow', add_id=True,
            highlight_edge='red',
            plot_kwargs={},
            animation_kwargs={}, saving_kwargs={}):

    def _update_graph(frame):
        for (i,j) in highlighted_edges:
            eid = graph.get_eid(i,j)
            graph_plot.patches[graph.vcount()+eid].set_color('k')
        for i in range(graph.vcount()):
            graph_plot.patches[i].set_facecolor(vertex_colors[frame][i])
            try:
                if (vertex_colors[frame-1][i] == 'white') and \
                (vertex_colors[frame][i] == 'orange'):
                    es = graph.es.select(_source=i)
                    for e in es:
                        j = e.source if e.source != i else e.target
                        if vertex_colors[frame][j] == highlight_edge:
                            eid = graph.get_eid(i, j)
                            graph_plot.patches[graph.vcount()+eid].set_color(highlight_edge)
                            highlighted_edges.append((i,j))
            except Exception:
                pass
        return ax.get_children()

    graph_plot = ig.plot(graph, target=ax, layout=graph_layout,
                         vertex_color=vertex_colors[0], **plot_kwargs)
    highlighted_edges = []

    if add_id:
        handles = ax.get_children()
        for i in range(graph.vcount()):
            center = handles[i].get_center()
            ax.text(center[0], center[1], str(i), ha='center', va='center')

    ani = animation.FuncAnimation(fig, _update_graph,
                                  frames, interval=interval,
                                  blit=blit, **animation_kwargs)
    ani.save(save_as, writer=writer, fps=fps, **saving_kwargs)

def plot_network(sim, ax, layer, vertices=None, **plot_kwargs):
    if vertices is not None:
        g = sim.population.network[layer].graph.subgraph(vertices)
    else:
        g = sim.population.network[layer].graph
    ig.plot(g, target=ax,
            **plot_kwargs)
