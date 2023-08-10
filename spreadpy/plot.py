import matplotlib.pyplot as plt


import matplotlib.animation as animation
import igraph as ig


def animate(fig, ax, graph, vertex_colors, layout, plot_kwargs={},
            animation_kwargs={}, saving_kwargs={}):

    def _update_graph(frame):
        for i in range(graph.vcount()):
            graph_plot.patches[i].set_facecolor(vertex_colors[frame][i])
        return ax.get_children()

    graph_plot = ig.plot(graph, target=ax, layout=layout,
                         vertex_color=vertex_colors[0], **plot_kwargs)

<<<<<<< Updated upstream
    ani = animation.FuncAnimation(fig, _update_graph, **animation_kwargs)
    ani.save(**saving_kwargs)
=======
    ani = animation.FuncAnimation(fig, _update_graph,
                                  frames, interval=interval,
                                  blit=blit, **animation_kwargs)
    ani.save(save_as, writer=writer, fps=fps, **saving_kwargs)

def plot(fig, ax):
    pass
>>>>>>> Stashed changes
