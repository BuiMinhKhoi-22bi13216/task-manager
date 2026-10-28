PRAGMA foreign_keys = ON;

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    owner_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (owner_id) REFERENCES users(id)
);

CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    title TEXT NOT NULL,
    description TEXT,

    task_type TEXT NOT NULL
        CHECK (task_type IN ('bug', 'feature', 'chore')),

    status TEXT NOT NULL DEFAULT 'TODO'
        CHECK (status IN ('TODO', 'IN_PROGRESS', 'DONE')),

    -- Khớp với TaskPriority trong domain: 1 = LOW, 2 = MEDIUM, 3 = HIGH.
    priority INTEGER NOT NULL DEFAULT 2
        CHECK (priority IN (1, 2, 3)),

    creator_id INTEGER,

    -- Domain (class Task) bắt buộc phải có người phụ trách.
    assignee_id INTEGER NOT NULL,
    due_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT,

    FOREIGN KEY (project_id)
        REFERENCES projects(id)
        ON DELETE CASCADE,

    FOREIGN KEY (creator_id)
        REFERENCES users(id),

    FOREIGN KEY (assignee_id)
        REFERENCES users(id)
);

CREATE INDEX idx_tasks_project_id
ON tasks(project_id);

CREATE INDEX idx_tasks_assignee_id
ON tasks(assignee_id);

CREATE INDEX idx_tasks_status
ON tasks(status);
