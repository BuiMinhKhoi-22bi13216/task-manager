PRAGMA foreign_keys = ON;

-- Chuỗi minh họa, chưa phải mật khẩu được hash thật.
INSERT INTO users (
    id, username, email, password_hash, full_name
)
VALUES
    (1, 'khoi', 'khoi@example.com', 'demo_hash_1', 'Khôi'),
    (2, 'an', 'an@example.com', 'demo_hash_2', 'An'),
    (3, 'linh', 'linh@example.com', 'demo_hash_3', 'Linh');

INSERT INTO projects (
    id, name, description, owner_id
)
VALUES
    (1, 'AI Camera', 'Dự án camera', 1),
    (2, 'Task Manager', 'Dự án quản lý công việc', 2);

INSERT INTO tasks (
    project_id,
    title,
    description,
    task_type,
    status,
    priority,
    creator_id,
    assignee_id,
    due_date
)
VALUES
    (
        1, 'Sửa lỗi kết nối camera', 'Kiểm tra kết nối',
        'bug', 'TODO', 3, 1, 2, '2026-10-25'
    ),
    (
        1, 'Thêm chức năng chụp ảnh', 'Lưu ảnh từ camera',
        'feature', 'IN_PROGRESS', 3, 1, 1, '2026-10-28'
    ),
    (
        1, 'Viết hướng dẫn cài đặt', NULL,
        'chore', 'DONE', 2, 1, 3, '2026-10-24'
    ),
    (
        1, 'Sửa lỗi hiển thị thời gian', NULL,
        'bug', 'IN_PROGRESS', 2, 1, 2, '2026-10-25'
    ),
    (
        1, 'Dọn thư mục log', NULL,
        'chore', 'TODO', 1, 1, 1, NULL
    ),
    (
        2, 'Thiết kế database', 'Tạo ba bảng',
        'feature', 'DONE', 3, 2, 1, '2026-10-26'
    ),
    (
        2, 'Sửa lỗi lọc trạng thái', NULL,
        'bug', 'TODO', 3, 2, 3, '2026-10-29'
    ),
    (
        2, 'Thêm chức năng tìm kiếm', 'Tìm theo tiêu đề',
        'feature', 'IN_PROGRESS', 3, 2, 2, '2026-10-30'
    ),
    (
        2, 'Bổ sung dữ liệu mẫu', NULL,
        'chore', 'DONE', 2, 2, 3, '2026-10-26'
    ),
    (
        2, 'Thêm bộ lọc hạn chót', NULL,
        'feature', 'TODO', 2, 2, 2, NULL
    );
