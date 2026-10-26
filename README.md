# Task Manager

Dự án thực hành Python trong quá trình thực tập tại VNPT Technology:
OOP, SOLID, Design Patterns, cấu trúc dữ liệu và xử lý ngoại lệ.

Chương trình chạy bằng demo trên terminal. Dữ liệu được lưu trong bộ nhớ
và mất khi chương trình kết thúc.

## Cài đặt

Yêu cầu Python 3.10 trở lên.

Chạy trong thư mục dự án trên WSL/Ubuntu:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Nhóm dev cài thêm Ruff và Mypy.

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

## Giới hạn

- Chưa có giao diện web hoặc API.
- Chưa lưu dữ liệu ra file hoặc cơ sở dữ liệu.
- Chưa gửi email/SMS thực tế.
- Chưa triển khai phân quyền; PermissionDeniedError đã được định nghĩa.
- Undo quản lý các thao tác được đưa qua CommandManager.