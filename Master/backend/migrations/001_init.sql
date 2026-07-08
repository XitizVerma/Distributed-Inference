-- Complete schema for the `distributed_inference` MySQL database.
--
-- This single file supersedes the old incremental migrations (001-006): every
-- ALTER from those steps has been folded into the CREATE TABLE below, so this
-- is the full end-state schema. Apply it once against a fresh database.

CREATE DATABASE IF NOT EXISTS distributed_inference
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE distributed_inference;

CREATE TABLE IF NOT EXISTS workers (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    hostname             VARCHAR(255) NOT NULL,
    node_name            VARCHAR(128),
    ip                   VARCHAR(64),
    gpu_info             VARCHAR(255),
    cpu_info             VARCHAR(255),
    total_memory_mb      INT,
    available_memory_mb  INT,
    worker_type          VARCHAR(32),
    models_available     JSON,
    status               ENUM('online', 'busy', 'offline') DEFAULT 'online',
    last_heartbeat_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    registered_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_workers_hostname (hostname)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tasks (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    prompt           TEXT NOT NULL,
    model_name       VARCHAR(128) NOT NULL,
    status           ENUM('queued', 'assigned', 'running', 'completed', 'failed') DEFAULT 'queued',
    input_url        VARCHAR(512) NULL,   -- blob input (image/pdf/etc.) the worker downloads
    result           TEXT,
    result_url       VARCHAR(512) NULL,   -- blob result stored in object storage
    result_mimetype  VARCHAR(128) NULL,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at       DATETIME NULL,
    completed_at     DATETIME NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS task_worker_map (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    task_id      INT NOT NULL,
    worker_id    INT NOT NULL,
    assigned_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    status       VARCHAR(32) DEFAULT 'assigned'
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS worker_metrics (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    worker_id           INT NOT NULL,
    recorded_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    cpu_percent         FLOAT,
    memory_percent      FLOAT,
    memory_used_mb      INT,
    gpu_percent         FLOAT NULL,
    gpu_memory_used_mb  INT NULL,
    INDEX idx_worker_metrics_worker_time (worker_id, recorded_at)
) ENGINE=InnoDB;

-- Backend-agnostic catalog of models the operator manages from Master.
CREATE TABLE IF NOT EXISTS models (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    backend     VARCHAR(64)  NOT NULL,   -- 'ollama' | 'huggingface' | ...
    task_type   VARCHAR(64)  NULL,       -- informational: 'text', 'text-to-image', ...
    params      JSON         NULL,       -- backend-specific hints
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Per-node install/uninstall/start/stop command queue, delivered via heartbeat.
CREATE TABLE IF NOT EXISTS model_commands (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    model_id      INT NOT NULL,
    worker_id     INT NOT NULL,
    action        ENUM('install', 'uninstall', 'start', 'stop') NOT NULL,
    status        ENUM('queued', 'sent', 'succeeded', 'failed') DEFAULT 'queued',
    error         TEXT NULL,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    sent_at       DATETIME NULL,
    completed_at  DATETIME NULL,
    INDEX idx_model_commands_worker_status (worker_id, status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS activity_log (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    worker_id   INT NULL,
    task_id     INT NULL,
    event_type  ENUM(
        'connected',
        'disconnected',
        'inference_accepted',
        'inference_completed',
        'task_created',
        'task_requeued',
        'model_command_created',
        'model_command_completed'
    ) NOT NULL,
    details     JSON,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
