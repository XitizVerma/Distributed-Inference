USE distributed_inference;

ALTER TABLE workers
    ADD COLUMN node_name VARCHAR(128) NULL AFTER hostname;
