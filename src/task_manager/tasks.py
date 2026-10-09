tasks: list[str] = []


def add_task(name: str) -> list[str]:
    tasks.append(name)
    return tasks


def remove_task(name: str) -> bool:
    if name in tasks:
        tasks.remove(name)
        return True
    return False
