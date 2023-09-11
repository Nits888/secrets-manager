-- Create the bucket_keys table with timestamps and constraint on bucket_name length
CREATE TABLE IF NOT EXISTS bucket_keys (
    bucket_name TEXT PRIMARY KEY CHECK(LENGTH(bucket_name) <= 255),
    client_id TEXT NOT NULL,
    encryption_key_salt BYTEA NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the secrets table with timestamps and foreign key constraint
CREATE TABLE IF NOT EXISTS secrets (
    bucket_name TEXT NOT NULL REFERENCES bucket_keys(bucket_name),
    secret_name TEXT NOT NULL,
    encrypted_secret BYTEA NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (bucket_name, secret_name)
);
