from task_manager.tasks import add_task, remove_task, tasks


def main() -> None:
    add_task("Learn Git")
    add_task("Learn Python")
    add_task("Learn AI")

    print("Before", add_task_list())

    remove_task("Learn Python")
    print("After", add_task_list())


def add_task_list() -> list[str]:
    return tasks


if __name__ == "__main__":
    main()
