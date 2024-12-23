CREATE TABLE if not exists subreddit_table (
    id TEXT,
    subreddit_id TEXT,
    created_date TIMESTAMP,
    ingestion_date TIMESTAMP,
    data JSONB
);


CREATE TABLE if not exists thread_table (
    id BIGINT,
    board varchar,
    last_modified TIMESTAMP,
    post_number BIGINT,
    ingestion_date TIMESTAMP,
    data JSONB,
    PRIMARY KEY (id, board)
);

CREATE TABLE if not exists posts (
    board varchar,
    thread_number BIGINT,
    post_number BIGINT,
    ingestion_date TIMESTAMP,
    data JSONB,
    PRIMARY KEY (board,thread_number, post_number)
);

CREATE TABLE if not exists toxic_table (
    subreddit_id TEXT,
    author_fullname VARCHAR,
    comment VARCHAR,
    created_date TIMESTAMP,
    ingestion_date TIMESTAMP,
    is_toxic BOOLEAN
);

ALTER TABLE subreddit_table
ADD COLUMN is_comment BOOLEAN;
