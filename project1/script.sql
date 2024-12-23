CREATE TABLE if not exists subreddit_table (
    id TEXT,
    subreddit_id TEXT,
    created_date TIMESTAMP,
    ingestion_date TIMESTAMP,
    data JSONB,
    PRIMARY KEY (id, subreddit_id)
);


CREATE TABLE if not exists thread_table (
    id BIGINT,
    board varchar,
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


