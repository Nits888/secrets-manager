-- Create the bucket_keys table with timestamps, constraints on bucket_name length, and app_name
CREATE TABLE IF NOT EXISTS bucket_keys (
    bucket_name TEXT NOT NULL CHECK(LENGTH(bucket_name) <= 255),
    app_name TEXT NOT NULL,
    client_id TEXT NOT NULL,
    encryption_key_salt BYTEA NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (bucket_name, app_name)
);

-- Create the secrets table with timestamps, foreign key constraint, and app_name
CREATE TABLE IF NOT EXISTS secrets (
    bucket_name TEXT NOT NULL,
    app_name TEXT NOT NULL,
    secret_name TEXT NOT NULL,
    encrypted_secret BYTEA NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (bucket_name, app_name, secret_name),
    FOREIGN KEY (bucket_name, app_name) REFERENCES bucket_keys(bucket_name, app_name)
);

