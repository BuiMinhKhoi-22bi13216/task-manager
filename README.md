# Task Manager

Dự án thực hành Python trong quá trình thực tập tại VNPT Technology:
OOP, SOLID, Design Patterns, cấu trúc dữ liệu, xử lý ngoại lệ, SQL, SQLite
và SQLAlchemy ORM.

Chương trình chạy bằng demo trên terminal. Phần domain (`main.py`) lưu dữ
liệu trong bộ nhớ; phần cơ sở dữ liệu (Ngày 8–10) lưu trong file SQLite
`SQL/task_manager.db`.

## Cài đặt

Yêu cầu Python 3.10 trở lên.

Chạy trong thư mục dự án trên WSL/Ubuntu:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Lệnh trên cài SQLAlchemy (dependency chính). Nhóm dev cài thêm Ruff và Mypy.

## Chạy chương trình

```bash
python main.py
```

Demo Factory, Builder, Decorator và Adapter:

```bash
python -m task_manager.design_pattern
```

Demo lấy tối đa 10 task ưu tiên cao nhất:

```bash
python -m task_manager.demo_top_tasks
```

Benchmark tìm kiếm 100.000 Task bằng list và dict:

```bash
python -m task_manager.benchmark_search
```

Kết quả được ghi vào task_manager/benchmark_ket_qua_ngay7.csv.

Thời gian đo phụ thuộc vào máy và từng lần chạy. Phép đo gồm chi phí
gọi hàm và lambda; tỷ lệ tốc độ chỉ mang tính tham khảo.

## Cơ sở dữ liệu SQLite (Ngày 8–10)

| File | Vai trò |
| --- | --- |
| `queries.sql` | Bài tập SQL Ngày 8, chạy trên database mẫu Chinook |
| `SQL/schema.sql` | Tạo 3 bảng `users`, `projects`, `tasks` |
| `SQL/example_data.sql` | Dữ liệu mẫu (3 user, 2 project, 10 task) |
| `SQL/task_manager.db` | Database dựng từ hai file trên |
| `sqlite_tasks.py` | CRUD task bằng `sqlite3` thuần, câu lệnh tham số hóa |
| `sql_injection_demo.py` | Minh họa SQL Injection và cách phòng tránh |
| `task_manager/orm_models.py` | Model SQLAlchemy 2.0 (`UserModel`, `ProjectModel`, `TaskModel`) |
| `task_manager/task_repository.py` | `TaskRepository`: add, get_by_id, list, update, delete |
| `task_manager/task_repository_port.py` | `TaskRepositoryPort` (Protocol) để service không phụ thuộc ORM |

Dựng lại database từ đầu (cần `sqlite3` CLI):

```bash
rm -f SQL/task_manager.db
sqlite3 SQL/task_manager.db < SQL/schema.sql
sqlite3 SQL/task_manager.db < SQL/example_data.sql
```

Quy ước ánh xạ giữa database và domain (schema có ràng buộc `CHECK` /
`NOT NULL` cho các trường trong bảng dưới):

| Cột | Giá trị | Domain |
| --- | --- | --- |
| `tasks.priority` | 1, 2, 3 | `LOW`, `MEDIUM`, `HIGH` |
| `tasks.task_type` | `bug`, `feature`, `chore` | `Task.task_type` |
| `tasks.status` | `TODO`, `IN_PROGRESS`, `DONE` | `TaskStatus` |
| `tasks.assignee_id` | bắt buộc (`NOT NULL`) | `Task.assignee` |

Chạy các script:

```bash
python sqlite_tasks.py          # CRUD sqlite3 thuần (tạo, đọc, sửa, xóa task tạm)
python sql_injection_demo.py    # SQL Injection: nối chuỗi và tham số hóa
python demo_connection.py       # Kết nối SQLAlchemy, đếm bản ghi
python demo_orm.py              # Đọc 3 task đầu bằng ORM
python demo_repository.py       # TaskService + TaskRepository (tự dọn dữ liệu thử)
python demo_n_plus_one.py       # Log SQL của truy vấn danh sách (đã sửa N+1)
```

Log SQL của SQLAlchemy mặc định tắt. Bật cho bất kỳ script nào bằng:

```bash
TASK_MANAGER_SQL_ECHO=1 python demo_repository.py
```

`n_plus_one_before.txt` và `n_plus_one_after.txt` là log trước và sau khi
thêm `selectinload`: danh sách 3 task giảm từ 1 + 3 truy vấn xuống 1 + 1.

Kiến trúc: `TaskService` → `TaskRepositoryPort` ← `TaskRepository` (SQLAlchemy).
`task_service.py` không import SQLAlchemy.

## Chức năng

- Tạo User, Project và Task.
- Factory tạo task bug, feature và chore với độ ưu tiên tương ứng.
- Builder thiết lập các thuộc tính tùy chọn của task.
- Project lưu Task bằng dict thông qua TaskStorage.
- Project tự cấp ID tăng dần, bắt đầu từ 1 trong từng project.
- ID do Project quản lý, không phải thuộc tính của Task.
- Tìm và xóa task theo ID.
- Sắp xếp theo priority, deadline hoặc thời điểm tạo.
- Thông báo khi trạng thái hoặc người phụ trách thay đổi.
- Hoàn tác thao tác qua CommandManager.
- Lấy top 10 task bằng heapq.
- Xử lý lỗi nghiệp vụ bằng custom exception.
- Lưu và đọc Task từ SQLite qua SQLAlchemy (Repository Pattern).
- CRUD bằng sqlite3 thuần và demo phòng chống SQL Injection.

Email và SMS chỉ mô phỏng bằng cách in ra terminal.

## Quy tắc Task

Luồng chuyển trạng thái thông thường:

```text
TODO → IN_PROGRESS → DONE
```

- Không cho phép chuyển trực tiếp từ TODO sang DONE.
- Không dùng change_status() để chuyển ngược từ DONE.
- Task DONE bị khóa các thuộc tính nghiệp vụ.
- Muốn chỉnh sửa phải gọi reopen() về TODO hoặc IN_PROGRESS.
- Undo thao tác hoàn thành task sử dụng reopen().
- Trước khi sửa trực tiếp ngoài CommandManager, gọi clear_history().

## Quản lý task theo ID

```python
task_id = project.add_task(task)
task = project.get_task(task_id)
optional_task = project.find_task(task_id)
removed_task = project.remove_task(task_id)
```

- get_task(): ném TaskNotFoundError khi không tìm thấy.
- find_task(): trả None khi không tìm thấy.
- remove_task(): ném TaskNotFoundError khi không tìm thấy.
- project.tasks trả list mới; chỉnh cấu trúc list này không thay đổi
  storage. Các đối tượng Task bên trong vẫn là những task đang được lưu.
- Thêm/xóa task bằng phương thức của Project.

## Design Patterns

| Pattern | Áp dụng |
| --- | --- |
| Factory | Tạo task theo loại |
| Builder | Thiết lập thuộc tính tùy chọn |
| Decorator | Đo thời gian thực thi |
| Adapter | Kết nối SMS mô phỏng với Notifier |
| Strategy | Thay đổi cách sắp xếp |
| Observer | Thông báo khi đổi trạng thái hoặc người phụ trách |
| Command | Thực hiện và hoàn tác thao tác |

TaskService nhận Notifier qua constructor để thực hành Dependency Injection.

## Độ phức tạp

N là số task; k là số task cần lấy.

| Thao tác | Độ phức tạp thời gian |
| --- | --- |
| Tìm ID trong list | O(N) trường hợp xấu nhất |
| Thêm, tìm hoặc xóa theo ID trong dict | O(1) trung bình |
| Lấy danh sách project.tasks | O(N), tạo list mới |
| Sắp xếp toàn bộ task | O(N log N) |
| Lấy top k bằng heapq, khi k nhỏ so với N | O(N log k) |
| Thêm command vào lịch sử | O(1) khấu hao, chưa tính thực thi |
| Lấy/xóa command cuối lịch sử | O(1), chưa tính undo và thông báo |

Chi phí thông báo còn phụ thuộc vào số Observer và công việc mỗi Observer làm.

## Kiểm tra

```bash
ruff check .
mypy
python -m unittest discover -s tests -v
```

Ruff và Mypy được cấu hình trong pyproject.toml.

Các test của `TaskRepository` (`tests/test_task_repository.py`) dùng database
tạm dựng từ `SQL/schema.sql` + `SQL/example_data.sql`, không ghi vào
`SQL/task_manager.db`. Nếu chưa cài SQLAlchemy, các test đó được bỏ qua.

## Giới hạn

- Chưa có giao diện web hoặc API.
- `main.py` vẫn chạy trong bộ nhớ; chỉ `TaskService` + `TaskRepository`
  (xem `demo_repository.py`) mới ghi vào SQLite.
- Domain chưa có khái niệm task chưa giao: mỗi task phải có assignee.
- Khi lưu qua Repository, dùng task_type `bug`, `feature` hoặc `chore`.
  `Task` và `TaskBuilder` mặc định tạo loại `general`; loại này chỉ dùng
  trong bộ nhớ, chưa được schema SQLite hỗ trợ. Có thể dùng `TaskFactory`
  để tạo task thuộc ba loại được hỗ trợ trước khi lưu vào database.
- Chưa gửi email/SMS thực tế.
- Chưa triển khai phân quyền; PermissionDeniedError đã được định nghĩa.
- Undo quản lý các thao tác được đưa qua CommandManager.
