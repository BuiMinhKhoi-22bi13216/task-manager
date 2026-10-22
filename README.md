# Task Manager

Dự án thực hành Python trong quá trình thực tập tại VNPT Technology, áp dụng OOP, SOLID, Design Patterns và cấu trúc dữ liệu.

Chương trình hiện chạy dưới dạng demo trên terminal. Dữ liệu được lưu trong bộ nhớ và không được giữ lại khi chương trình kết thúc.

## Yêu cầu

- Python 3.10 trở lên.
- Git.
- Khuyến nghị sử dụng virtual environment.

## Cài đặt

Chạy các lệnh sau trong thư mục dự án:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Nhóm `dev` cài thêm Ruff và Mypy để kiểm tra code.

## Chạy chương trình

```bash
python main.py
```

Chạy demo lấy 10 task có độ ưu tiên cao nhất:

```bash
python -m task_manager.demo_top_tasks
```

Chạy benchmark tìm kiếm 100.000 task bằng list và dict:

```bash
python -m task_manager.benchmark_search
```

Benchmark xuất kết quả ra file CSV. Thời gian đo phụ thuộc vào máy và từng lần chạy.

## Chức năng

- Tạo task với tiêu đề, người phụ trách, trạng thái và độ ưu tiên.
- Quản lý danh sách task trong project.
- Chuyển trạng thái, giao task và mở lại task đã hoàn thành.
- Sắp xếp task theo độ ưu tiên, deadline hoặc thời điểm tạo.
- Thông báo khi trạng thái hoặc người phụ trách thay đổi.
- Hoàn tác các thao tác được thực hiện qua CommandManager.
- Lưu và tra cứu task theo ID bằng dict.
- Lấy 10 task ưu tiên cao nhất bằng heapq.
- Xử lý lỗi nghiệp vụ bằng custom exception.

Email và SMS trong dự án chỉ là mô phỏng bằng cách in ra terminal.

## Quy tắc nghiệp vụ

Luồng trạng thái thông thường:

```text
TODO → IN_PROGRESS → DONE
```

- Không cho phép chuyển trực tiếp từ TODO sang DONE.
- Không cho phép dùng change_status() để chuyển ngược từ DONE.
- Task ở trạng thái DONE bị khóa các thuộc tính nghiệp vụ.
- Muốn sửa task đã hoàn thành, phải gọi reopen() để đưa về TODO hoặc IN_PROGRESS.
- Khi hoàn tác thao tác hoàn thành task, chương trình sử dụng reopen().
- Nếu sửa task trực tiếp ngoài CommandManager, cần xóa lịch sử bằng clear_history() trước để tránh dùng lịch sử undo cũ.

## Design Patterns đã áp dụng

| Pattern | Mục đích |
| --- | --- |
| Factory | Tạo task loại bug, feature và chore với độ ưu tiên tương ứng |
| Builder | Tạo task theo từng bước và thiết lập thuộc tính tùy chọn |
| Decorator | Đo thời gian thực thi hàm |
| Adapter | Kết nối giao diện SMS mô phỏng với Notifier |
| Strategy | Thay đổi cách sắp xếp task |
| Observer | Phát thông báo khi task thay đổi |
| Command | Đóng gói thao tác và hỗ trợ undo |

TaskService nhận các Notifier từ bên ngoài qua constructor để thực hành Dependency Injection.

## Cấu trúc chính

```text
Task-manager/
├── main.py
├── pyproject.toml
├── README.md
├── task_manager/
│   ├── __init__.py
│   ├── models.py
│   ├── project.py
│   ├── task_factory.py
│   ├── builder.py
│   ├── decorator.py
│   ├── notifier.py
│   ├── external_sms.py
│   ├── sms_adapter.py
│   ├── strategies.py
│   ├── task_observer.py
│   ├── commands.py
│   ├── task_service.py
│   ├── task_storage.py
│   ├── taskdisplayer.py
│   ├── top_tasks.py
│   ├── demo_top_tasks.py
│   ├── benchmark_search.py
│   └── exceptions.py
└── tests/
```

## Kiểm tra code

Kiểm tra lỗi và import bằng Ruff:

```bash
ruff check .
```

Kiểm tra kiểu dữ liệu bằng Mypy:

```bash
mypy
```

Chạy toàn bộ unit test:

```bash
python -m unittest discover -s tests -v
```

Cấu hình Ruff và Mypy nằm trong pyproject.toml.

## Giới hạn hiện tại

- Chưa có giao diện web hoặc API.
- Chưa lưu dữ liệu vào file hay cơ sở dữ liệu.
- Chưa gửi email hoặc SMS thực tế.
- Undo chỉ quản lý các thao tác được đưa qua CommandManager.