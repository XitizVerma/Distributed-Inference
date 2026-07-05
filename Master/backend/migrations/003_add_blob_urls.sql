USE distributed_inference;

ALTER TABLE tasks
    ADD COLUMN input_url VARCHAR(512) NULL AFTER status,
    ADD COLUMN result_url VARCHAR(512) NULL AFTER result,
    ADD COLUMN result_mimetype VARCHAR(128) NULL AFTER result_url;
