CREATE TABLE IF NOT EXISTS objects (
    id SERIAL PRIMARY KEY,
    policy_id INT NOT NULL,
    run_id INT NOT NULL,
    step_name TEXT NOT NULL,
    object_name TEXT NOT NULL,
    value BYTEA, 
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);