USE distributed_inference;

ALTER TABLE workers
    ADD COLUMN worker_type VARCHAR(32) NULL AFTER available_memory_mb;

ALTER TABLE activity_log
    MODIFY COLUMN event_type ENUM(
        'connected',
        'disconnected',
        'inference_accepted',
        'inference_completed',
        'task_created',
        'task_requeued'
    ) NOT NULL;
