import matplotlib.pyplot as plt


import matplotlib.animation as animation
import igraph as ig


def animate(fig, ax, graph, vertex_colors, graph_layout,
            frames, save_as, interval=500, blit=True, fps=60,
            writer='pillow', add_id=True,
            plot_kwargs={},
            animation_kwargs={}, saving_kwargs={}):

    def _update_graph(frame):
        for i in range(graph.vcount()):
            graph_plot.patches[i].set_facecolor(vertex_colors[frame][i])
        return ax.get_children()

    graph_plot = ig.plot(graph, target=ax, layout=graph_layout,
                         vertex_color=vertex_colors[0], **plot_kwargs)
    
    if add_id:
        handles = ax.get_children()
        for i in range(graph.vcount()):
            center = handles[i].get_center()
            ax.text(center[0], center[1], str(i), ha='center', va='center')

    ani = animation.FuncAnimation(fig, _update_graph,
                                  frames, interval=interval,
                                  blit=blit, **animation_kwargs)
    ani.save(save_as, writer=writer, fps=fps, **saving_kwargs)
