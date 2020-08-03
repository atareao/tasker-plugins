#!/usr/bin/env python
try:
    import logging

    FORMAT = "%(asctime)-15s %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        filename="log.log",
        format=FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    import json
    from config_browser_integration import Configurator
    from messenger import Messenger
    import todotxtio
    import time
    import datetime
    import re
except BaseException:
    logging.exception("Uncaught exception")

messenger = Messenger()


def searchTodo(todoToSearch):
    conf = Configurator()
    list_of_todos = todotxtio.from_file(conf.todo)
    for todo in list_of_todos:
        if todo.text == todoToSearch:
            return todo


def getTagsAfterStopIfNeeded(todo):
    beforeTags = {}
    if todo:
        beforeTags = todo.tags
    started_at = float(beforeTags.get("started_at", 0))
    newTags = beforeTags
    if started_at:
        just_now = time.time()
        trackHistory(todo, just_now)
        total_time = (
            float(beforeTags.get("total_time", 0)) + just_now - started_at
        )
        newTags["started_at"] = "0"
        newTags["total_time"] = str(total_time)
    return newTags


def getTagsAfterChangeState(todo):
    beforeTags = {}
    if todo:
        beforeTags = todo.tags
    started_at = float(beforeTags.get("started_at", 0))
    just_now = time.time()
    newTags = beforeTags
    if started_at:
        total_time = (
            float(beforeTags.get("total_time", 0)) + just_now - started_at
        )
        trackHistory(todo, just_now)
        newTags["started_at"] = "0"
        newTags["total_time"] = str(total_time)
    else:
        newTags["started_at"] = str(just_now)
    return newTags


def trackHistory(todo, just_now):
    beforeTags = {}
    if todo:
        beforeTags = todo.tags
    started_at = float(beforeTags.get("started_at", 0))
    conf = Configurator()
    list_of_history = todotxtio.from_file(conf.todo_histoy)
    new_todo_history = todotxtio.Todo(text=todo.text)
    new_todo_history.projects = todo.projects
    new_todo_history.contexts = todo.contexts
    new_todo_history.completed = True
    new_todo_history.tags["started"] = str(started_at)
    new_todo_history.tags["ended"] = str(just_now)
    new_todo_history.tags["step_time"] = str(just_now - started_at)
    new_todo_history.tags["total_time"] = str(
        float(todo.tags.get("total_time", 0)) + (just_now - started_at)
    )
    desc = formatTodo(todo.tags.get("description"))
    if desc:
        new_todo_history.tags["description"] = desc
    list_of_history.append(new_todo_history)
    todotxtio.to_file(conf.todo_histoy, list_of_history)


def formatTodo(str):
    res = str
    if res:
        expression = r"\s"
        res = re.sub(expression, "_", res)
    return res


def changeState(payload):
    todo = searchTodo(payload["todo"])
    desc = formatTodo(payload.get("description"))
    if not todo:
        creation_date = datetime.datetime.now().strftime("%Y-%m-%d")
        newTodo = todotxtio.Todo(
            text=payload["todo"], creation_date=creation_date
        )
        if payload.get("project"):
            newTodo.projects = [
                formatTodo(payload["project"]),
            ]
        if payload.get("context"):
            newTodo.contexts = [
                formatTodo(payload["context"]),
            ]
        if desc:
            newTodo.tags["description"] = desc
        newTodo.tags = getTagsAfterChangeState(newTodo)
        includeTodo(newTodo)
    else:
        if desc:
            todo.tags["description"] = desc
        todo.tags = getTagsAfterChangeState(todo)
        saveTodo(todo)
    messenger.sendMessage({"type": "stateChanged", "todo": payload["todo"]})


def includeTodo(todoToAdd):
    conf = Configurator()
    list_of_todos = todotxtio.from_file(conf.todo)
    for i in range(len(list_of_todos)):
        list_of_todos[i].tags = getTagsAfterStopIfNeeded(list_of_todos[i])
    list_of_todos.append(todoToAdd)
    todotxtio.to_file(conf.todo, list_of_todos)


def saveTodo(todoToChange):
    conf = Configurator()
    list_of_todos = todotxtio.from_file(conf.todo)
    for i in range(len(list_of_todos)):
        if list_of_todos[i].text == todoToChange.text:
            list_of_todos[i].tags = todoToChange.tags
        else:
            list_of_todos[i].tags = getTagsAfterStopIfNeeded(list_of_todos[i])
    todotxtio.to_file(conf.todo, list_of_todos)


def sendState(todoText):
    todo = searchTodo(todoText)
    if not todo:
        messenger.sendMessage(
            {"type": "stateGetted", "todo": todoText, "state": "paused"}
        )
    else:
        if (
            todo.text == todoText
            and todo.tags["started_at"]
            and float(todo.tags["started_at"]) > 0
        ):
            messenger.sendMessage(
                {"type": "stateGetted", "todo": todoText, "state": "started"}
            )
        else:
            messenger.sendMessage(
                {"type": "stateGetted", "todo": todoText, "state": "paused"}
            )


try:
    # Main Loop
    while True:
        receivedMessage = messenger.getMessage()
        if receivedMessage:
            dictMessage = json.loads(receivedMessage)
            logging.debug("Received: " + receivedMessage)
            payload = dictMessage["payload"]
            if dictMessage["type"] == "getState":
                sendState(payload["todo"])
            elif dictMessage["type"] == "changeState":
                changeState(payload)
except BaseException:
    logging.exception("Uncaught exception")
