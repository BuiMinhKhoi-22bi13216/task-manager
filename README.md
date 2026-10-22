# Task Manager — bản sửa sau rà soát

Project Python OOP với Task/User/Project, Factory, Builder, Decorator, Adapter,
Strategy, Observer, Command, lưu dict và lấy Top 10 bằng heapq.

## Chạy trên WSL/Ubuntu

Yêu cầu Python 3.10 trở lên; đã kiểm tra bằng Python 3.12.14. Chỉ dùng thư viện
chuẩn của Python, không cần cài thêm package. Mở terminal tại thư mục có `main.py`:

```bash
python3 main.py
python3 -m unittest discover -v
python3 -m unittest discover -s tests -v
python3 -m task_manager.design_pattern
python3 -m task_manager.demo_top_tasks
python3 -m task_manager.benchmark_search
```

Benchmark vẫn hỗ trợ chạy trực tiếp `python3 benchmark_search.py` khi terminal
đang ở trong thư mục `task_manager`. Nó ghi đè CSV kết quả mỗi lần chạy; số đo
phụ thuộc máy và tải hệ thống.

## Quy tắc Task

- Luồng thường: `TODO → IN_PROGRESS → DONE`; không bỏ qua IN_PROGRESS.
- DONE không cho gán/xóa các trường nghiệp vụ. Muốn sửa: `task.reopen()` trước.
- Chỉ `reopen()` được đưa task từ DONE về IN_PROGRESS hoặc TODO.
- Undo hoàn thành cũng gọi `reopen(IN_PROGRESS)` và gửi đúng một event reopened.
- Undo IN_PROGRESS về TODO là rollback có kiểm soát của Command, không phải một
  chuyển trạng thái thường qua `change_status()`.
- Task nhận status/priority bằng Enum và assignee bằng User; không nhận chuỗi thay
  cho các kiểu đó. Trường title, task_type và tên User không được rỗng.
- Deadline là `date` hoặc `None`, không nhận `datetime`. `created_at` là datetime
  không gắn múi giờ, thống nhất với dữ liệu cũ; muốn nhận dữ liệu có múi giờ, hãy
  chuẩn hóa chúng ở nơi đọc dữ liệu trước khi tạo/chỉnh Task.
- User là giá trị bất biến: không gán `task.assignee.name`. Thay người thực hiện
  bằng `task.assign_to(User("Tên mới"))`; nếu Task DONE phải reopen trước.
- `task.assignee = User(...)` vẫn được hỗ trợ, có kiểm tra và gửi event một lần.
- Sửa title/description/priority/deadline trực tiếp có kiểm tra, nhưng không tự
  gửi event: bộ Observer hiện tập trung vào status/assign/reopen/undo.

## Builder, Observer và Factory

`TaskBuilder.from_task(task).build()` tạo một đối tượng mới và giữ `created_at`.
Nếu nguồn là DONE, chỉ cho dựng bản sao giữ nguyên dữ liệu. Muốn chỉnh dữ liệu,
gọi `task.reopen()` trước rồi mới tạo Builder từ task đó. Builder không sửa Task
nguồn và không sao chép các subscription.

`TaskService(strategy, notifiers=[...])` vẫn hoạt động như cũ. Có thể inject observer
trực tiếp bằng `TaskService(strategy, observers=[...])`; hai danh sách có thể dùng
cùng lúc. Không truyền cùng một notifier qua hai đường nếu không muốn nhận hai
thông báo do hai observer khác nhau.

`watch_project(project)` đăng ký các task đang có. Khi thêm task sau đó, dùng
`service.add_task(project, task)` để vừa thêm vừa đăng ký; hoặc gọi
`project.add_task(task)` rồi `service.watch_task(task)`.

`PrefixNotifier(notifier, "[Task Manager] ")` bọc mọi Notifier mà không sửa class
gốc; có thể đưa vào NotifierObserver. Function decorator đo thời gian vẫn giữ.

Factory có sẵn bug/HIGH, feature/MEDIUM và chore/LOW. Muốn bổ sung loại:

```python
TaskFactory.register_type("research", TaskPriority.HIGH)
task = TaskFactory.create_task("research", "Read paper", User("An"))
```

Đăng ký trùng loại sẽ bị từ chối. Bảng rank priority được dùng chung cho Strategy
và TopTasks. Strategy created_at ưu tiên mới nhất; TopTasks dùng task cũ hơn làm
tie breaker sau priority/deadline.

## Undo và xung đột

Command lưu một token của trạng thái Task, ngoài giá trị status/assignee. Mỗi
thay đổi nghiệp vụ tạo token mới. Vì thế complete → reopen hoặc đổi người rồi
đổi lại vẫn làm undo cũ báo `UndoConflictError`, kể cả khi giá trị cuối giống cũ.

Khi undo hợp lệ, token của bước trước được khôi phục để undo nhiều bước LIFO
tiếp tục hoạt động; `revision` vẫn chỉ tăng. Thay đổi task trong callback Observer
không bị xem nhầm là thay đổi thuộc quyền của Command. Callback nên ưu tiên ghi
nhận/gửi thông báo thay vì chỉnh nghiệp vụ.

`CommandStateError` và `UndoConflictError` thuộc `TaskManagerError`, đồng thời
tương thích với các chỗ bắt `RuntimeError` trong test cũ. Undo bị từ chối giữ
nguyên history. Không cần bỏ khóa DONE để hỗ trợ undo.

## Phạm vi

Email và SMS ở đây là mô phỏng bằng print/list, chưa gửi qua nhà cung cấp thật.
TaskStorage vẫn trả None khi thiếu ID để giữ hợp đồng benchmark. Chưa bổ sung
database/API/phân quyền ngoài phạm vi project. Chạy toàn bộ test trước khi commit
và xem `NHAT_KY_SUA_LOI.txt` để biết từng file/vị trí đã đổi.
