"""So sánh tìm kiếm bằng list và dict với 100.000 task."""

import csv
import sys
from collections.abc import Callable
from pathlib import Path
from statistics import median
from time import perf_counter

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from task_manager.models import Task, TaskPriority, TaskStatus, User
from task_manager.task_storage import TaskStorage

TASK_COUNT = 100_000


def create_sample_tasks(count: int) -> list[tuple[int, Task]]:
    user = User("Benchmark")
    return [
        (task_id, Task(f"Task {task_id}", user, TaskStatus.TODO, TaskPriority.MEDIUM))
        for task_id in range(1, count + 1)
    ]


def find_task_in_list(tasks: list[tuple[int, Task]], task_id: int) -> Task | None:
    for current_id, task in tasks:
        if current_id == task_id:
            return task
    return None


def measure_microseconds(
    action: Callable[[], object],
    repetitions: int,
    rounds: int = 5,
) -> float:
    samples = []

    for _ in range(rounds):
        start = perf_counter()

        for _ in range(repetitions):
            action()

        elapsed = perf_counter() - start
        samples.append(elapsed * 1_000_000 / repetitions)

    return median(samples)


def main() -> None:
    tasks = create_sample_tasks(TASK_COUNT)
    storage = TaskStorage()

    start = perf_counter()

    for task_id, task in tasks:
        storage.add_task(task_id, task)

    build_ms = (perf_counter() - start) * 1000

    assert len(tasks) == len(storage) == TASK_COUNT

    cases = [
        ("Dau danh sach", 1),
        ("Giua danh sach", TASK_COUNT // 2),
        ("Cuoi danh sach", TASK_COUNT),
        ("ID khong ton tai", TASK_COUNT + 1),
    ]

    print(f"So task: {TASK_COUNT:,}")
    print(f"Thoi gian xay dict: {build_ms:.3f} ms")
    print(f"{'Truong hop':<20} {'List (us)':>12} {'Dict (us)':>12} {'Nhanh hon':>12}")

    results = []

    for label, task_id in cases:
        assert find_task_in_list(tasks, task_id) == storage.find_task(task_id)

        list_us = measure_microseconds(
            lambda: find_task_in_list(tasks, task_id),
            repetitions=30,
        )

        dict_us = measure_microseconds(
            lambda: storage.find_task(task_id),
            repetitions=20_000,
        )

        ratio = list_us / dict_us if dict_us else float("inf")

        print(f"{label:<20} {list_us:>12.3f} {dict_us:>12.3f} {ratio:>11.1f}x")

        results.append(
            {
                "truong_hop": label,
                "task_id": task_id,
                "list_us": round(list_us, 4),
                "dict_us": round(dict_us, 4),
                "nhanh_hon_lan": round(ratio, 2),
            }
        )

    output = Path(__file__).with_name("benchmark_ket_qua_ngay7.csv")

    with output.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=results[0].keys(),
        )
        writer.writeheader()
        writer.writerows(results)

    print(f"Da luu ket qua: {output.name}")


if __name__ == "__main__":
    main()