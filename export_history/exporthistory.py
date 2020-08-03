import csv
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

# Custom featured needed
import gi
import pluggy
import todotxtio
from alert import Alert
from configurator import Configuration
from gi.repository import Gtk
from hooks import IndicatorSpec

# Decorator for hook. The function that was decorated with this
# will be called from de master source if it in Hookspecks availables
indicatorimpl = pluggy.HookimplMarker("indicator")


try:
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    gi.require_version("AppIndicator3", "0.1")
except Exception as e:
    print(e)
    exit(-1)


class ExportingHistory(IndicatorSpec):
    def __init__(self,):
        configuration = Configuration()
        preferences = configuration.get("preferences")
        parent_folder = Path(
            os.path.expanduser(preferences["todo-file"])
        ).parent.as_posix()
        self.todo_histoy = parent_folder + os.sep + "todo.history.txt"
        self.export_file = parent_folder + os.sep + "export.csv"

    @indicatorimpl
    def get_hook_menu(self,):
        history_export = Gtk.MenuItem.new_with_label("History track export")
        history_export.connect("activate", self.export_history)

        history_clear = Gtk.MenuItem.new_with_label("History track clear")
        history_clear.connect("activate", self.clear_history)

        return [history_export, history_clear]

    def clear_history(self, widget):
        widget.set_sensitive(False)
        result = Alert.show_alert(
            "Are you sure?", "You will remove all history", True
        )
        if result == Gtk.ResponseType.OK:
            todotxtio.to_file(self.todo_histoy, [])
        widget.set_sensitive(True)

    def timestam2datetime(self, timestamp):
        return datetime.datetime.fromtimestamp(float(timestamp))

    def datetime2timestr(self, dt):
        return dt.strftime("%H:%M:%S")

    def datetime2datestr(self, dt):
        return dt.strftime("%d-%m-%Y")

    def export_history(self, widget):
        widget.set_sensitive(False)
        history_items = todotxtio.from_file(self.todo_histoy)
        history_items.sort(
            key=lambda todo: (
                sorted(todo.contexts),
                sorted(todo.projects),
                todo.text,
                todo.tags["started"],
            )
        )
        if history_items:
            f = open(self.export_file, "w")

            with f:
                fnames = [
                    "context",
                    "project",
                    "todo",
                    "description",
                    "started_date",
                    "started_time",
                    "ended_date",
                    "ended_time",
                    "step_time",
                    "accumulated_time",
                    "total_time_after_step",
                ]
                writer = csv.DictWriter(f, fnames)

                writer.writeheader()
                previous_todo = history_items[0].text
                accumulated_time = 0
                for history_item in history_items:
                    started = self.timestam2datetime(
                        history_item.tags["started"]
                    )
                    ended = self.timestam2datetime(history_item.tags["ended"])

                    # Localized time
                    step = (
                        self.timestam2datetime(history_item.tags["step_time"])
                        - self.timestam2datetime(0)
                    ).total_seconds()
                    total = (
                        self.timestam2datetime(history_item.tags["total_time"])
                        - self.timestam2datetime(0)
                    ).total_seconds()
                    if previous_todo != history_item.text:
                        accumulated_time = 0
                        previous_todo = history_item.text
                    accumulated_time += step
                    writer.writerow(
                        {
                            "context": re.sub(
                                "_", " ", history_item.contexts[0]
                            )
                            if len(history_item.contexts)
                            else "",
                            "project": re.sub(
                                "_", " ", history_item.projects[0]
                            )
                            if len(history_item.projects)
                            else "",
                            "todo": history_item.text,
                            "description": re.sub(
                                "_",
                                " ",
                                history_item.tags.get("description", ""),
                            ),
                            "started_date": self.datetime2datestr(started),
                            "started_time": self.datetime2timestr(started),
                            "ended_date": self.datetime2datestr(ended),
                            "ended_time": self.datetime2timestr(ended),
                            "step_time": str(
                                datetime.timedelta(seconds=round(step, 0))
                            ),
                            "accumulated_time": str(
                                datetime.timedelta(
                                    seconds=round(accumulated_time, 0)
                                )
                            ),
                            "total_time_after_step": str(
                                datetime.timedelta(seconds=round(total, 0))
                            ),
                        }
                    )

            if sys.platform.startswith("linux"):
                subprocess.call(["xdg-open", self.export_file])
            else:
                os.startfile(self.export_file)
        else:
            Alert.show_alert("Your history is clean")
        widget.set_sensitive(True)
