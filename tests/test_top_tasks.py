"""Day 7 Phase 1 tests"""

import random
import unittest
from datetime import date, datetime, timedelta

from task_manager.models import Task, TaskPriority, TaskStatus, User
from task_manager.top_tasks import top_tasks, urgency_key


class TestTopTasks(unittest.TestCase):
    def setUp(self) -> None:
        self.user = User("Intern")
        self.base_time = datetime(2026, 10, 21, 8, 0)

    def make_task(
        self,
        title: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        status: TaskStatus = TaskStatus.TODO,
        deadline: date | None = None,
        created_at: datetime | None = None,
    ) -> Task:
        return Task(
            title=title,
            assignee=self.user,
            priority=priority,
            status=status,
            deadline=deadline,
            created_at=created_at or self.base_time,
        )

    def assert_same_objects(self, actual, expected):
        self.assertEqual([id(t) for t in actual], [id(t) for t in expected])

    def test_priority_high_medium_low(self):
        low = self.make_task("low", TaskPriority.LOW)
        high = self.make_task("high", TaskPriority.HIGH)
        medium = self.make_task("medium", TaskPriority.MEDIUM)
        self.assert_same_objects(top_tasks([low, medium, high]), [high, medium, low])

    def test_deadline_before_missing_and_earliest_first(self):
        missing = self.make_task("none", deadline=None)
        late = self.make_task("late", deadline=date(2026, 12, 10))
        early = self.make_task("early", deadline=date(2026, 11, 1))
        self.assert_same_objects(
            top_tasks([missing, late, early]), [early, late, missing]
        )

    def test_older_created_at_first(self):
        newer = self.make_task("new", created_at=datetime(2026, 10, 22))
        older = self.make_task("old", created_at=datetime(2026, 10, 2))
        self.assert_same_objects(top_tasks([newer, older]), [older, newer])

    def test_done_excluded_by_default(self):
        done = self.make_task("done", TaskPriority.HIGH, TaskStatus.DONE)
        todo = self.make_task("todo", TaskPriority.MEDIUM)
        self.assert_same_objects(top_tasks([done, todo]), [todo])
        self.assert_same_objects(
            top_tasks([done, todo], include_done=True), [done, todo]
        )

    def test_zero_and_negative_n(self):
        task = self.make_task("one")
        self.assertEqual(top_tasks([task], 0), [])
        self.assertEqual(top_tasks([task], -2), [])

    def test_empty_and_n_larger_than_input(self):
        self.assertEqual(top_tasks([], 10), [])
        tasks = [self.make_task("a"), self.make_task("b")]
        self.assertEqual(len(top_tasks(tasks, 10)), 2)

    def test_equal_keys_do_not_compare_tasks_and_stable_order(self):
        tasks = [self.make_task(str(i)) for i in range(4)]
        self.assert_same_objects(top_tasks(tasks, 3), tasks[:3])

    def test_input_unchanged(self):
        tasks = [
            self.make_task("low", TaskPriority.LOW),
            self.make_task("high", TaskPriority.HIGH),
        ]
        before = [id(x) for x in tasks]
        top_tasks(tasks, 1)
        self.assertEqual([id(x) for x in tasks], before)

    def test_randomized_sorted_oracle(self):
        randomizer = random.Random(42)
        statuses = list(TaskStatus)
        priorities = list(TaskPriority)
        tasks = []
        for i in range(500):
            deadline = (
                date(2026, 11, 1) + timedelta(days=randomizer.randrange(20))
                if randomizer.randrange(3)
                else None
            )
            tasks.append(
                self.make_task(
                    str(i),
                    priority=randomizer.choice(priorities),
                    status=randomizer.choice(statuses),
                    deadline=deadline,
                    created_at=self.base_time + timedelta(days=randomizer.randrange(8)),
                )
            )
        expected = sorted(
            (t for t in tasks if t.status != TaskStatus.DONE),
            key=urgency_key,
        )[:10]
        self.assert_same_objects(top_tasks(tasks), expected)


if __name__ == "__main__":
    unittest.main()
