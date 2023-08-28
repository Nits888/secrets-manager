CREATE TABLE IF NOT EXISTS bucket_keys (
    bucket_name TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    client_secret TEXT NOT NULL,
    encryption_key BYTEA NOT NULL
);

CREATE TABLE IF NOT EXISTS secrets (
    bucket_name TEXT NOT NULL,
    secret_name TEXT NOT NULL,
    encrypted_secret BYTEA NOT NULL,
    PRIMARY KEY (bucket_name, secret_name)
);
