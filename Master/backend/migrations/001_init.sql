CREATE DATABASE IF NOT EXISTS distributed_inference
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE distributed_inference;

CREATE TABLE IF NOT EXISTS workers (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    hostname             VARCHAR(255) NOT NULL,
    ip                   VARCHAR(64),
    gpu_info             VARCHAR(255),
    cpu_info             VARCHAR(255),
    total_memory_mb      INT,
    available_memory_mb  INT,
    models_available     JSON,
    status               ENUM('online', 'busy', 'offline') DEFAULT 'online',
    last_heartbeat_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    registered_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_workers_hostname (hostname)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tasks (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    prompt        TEXT NOT NULL,
    model_name    VARCHAR(128) NOT NULL,
    status        ENUM('queued', 'assigned', 'running', 'completed', 'failed') DEFAULT 'queued',
    result        TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at    DATETIME NULL,
    completed_at  DATETIME NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS task_worker_map (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    task_id      INT NOT NULL,
    worker_id    INT NOT NULL,
    assigned_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    status       VARCHAR(32) DEFAULT 'assigned'
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS activity_log (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    worker_id   INT NULL,
    task_id     INT NULL,
    event_type  ENUM('connected', 'disconnected', 'inference_accepted', 'inference_completed', 'task_created') NOT NULL,
    details     JSON,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
