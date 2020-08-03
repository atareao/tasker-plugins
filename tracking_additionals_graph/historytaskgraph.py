#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of tasker
#
# Copyright (c) 2020 Lorenzo Carbonell Cerezo <a.k.a. atareao>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import datetime
import os
from pathlib import Path

import todotxtio
from basegraph import BaseGraph
from configurator import Configuration


class HistoryTaskGraph(BaseGraph):
    def __init__(self, title=""):
        configuration = Configuration()
        preferences = configuration.get("preferences")
        self.todo_histoy = (
            Path(
                os.path.expanduser(preferences["todo-file"])
            ).parent.as_posix()
            + os.sep
            + "todo.history.txt"
        )
        BaseGraph.__init__(self, title, "")
        self.subtitle = ""

    def get_plaindata(self,):
        return todotxtio.from_file(self.todo_histoy)

    def get_keys(self, list_of_todos):
        days = []
        for todo in list_of_todos:
            day = self.timestam2datestr(todo.tags["started"])
            if day not in days:
                days.append(day)
        days.sort()
        return days

    def get_values(self, days, list_of_todos):
        values = []
        list_of_todos.sort(
            key=lambda todo: (
                self.timestam2datestr(todo.tags["started"]),
                sorted(todo.projects),
                todo.text,
            )
        )
        i = 0
        for todo in list_of_todos:
            data = []
            for day in days:
                if day == self.timestam2datestr(todo.tags["started"]):
                    data.append(
                        float(todo.tags.get("step_time", "0")) / 3600.0
                    )
                else:
                    data.append(0)
            previous_data = list(
                filter(lambda item: item["name"] == todo.text, values)
            )
            if previous_data:
                j = 0
                for item in previous_data[0]["data"]:
                    data[j] += item
                    j += 1
                values[previous_data[0]["index"]]["data"] = data
            else:
                values.append({"index": i, "name": todo.text, "data": data})
                i += 1
        return values

    def timestam2datestr(self, timestamp):
        return datetime.date.fromtimestamp(float(timestamp)).strftime(
            "%Y-%m-%d"
        )


if __name__ == "__main__":
    graph = HistoryTaskGraph("Testing graph")
    graph.run()
