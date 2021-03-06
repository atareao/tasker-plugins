# Custom featured needed
import gi
import pluggy
from gi.repository import Gtk
from hooks import IndicatorSpec

from .historytaskgraph import HistoryTaskGraph

# Decorator for hook. The function that was decorated with this
# will be called from de master source if it in Hookspecks availables
indicatorimpl = pluggy.HookimplMarker("indicator")


try:
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    gi.require_version("AppIndicator3", "0.1")
    gi.require_version("GdkPixbuf", "2.0")
    gi.require_version("Keybinder", "3.0")
except Exception as e:
    print(e)
    exit(-1)


class TrackingHistoryGraph(IndicatorSpec):
    @indicatorimpl
    def get_hook_menu(self,):
        history_item = Gtk.MenuItem.new_with_label("History track graph")
        history_item.connect("activate", self.show_graph)

        return history_item

    def show_graph(self, widget):
        widget.set_sensitive(False)

        title = "Timetracking tasker"

        graph = HistoryTaskGraph(title)
        graph.run()
        graph.destroy()
        widget.set_sensitive(True)
