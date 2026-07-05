USE distributed_inference;

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
