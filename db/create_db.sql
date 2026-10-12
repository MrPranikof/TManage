CREATE ROLE tmanage WITH LOGIN PASSWORD 'change_me';
CREATE DATABASE tmanage OWNER tmanage;

\c tmanage tmanage

CREATE TYPE user_role AS ENUM ('user', 'admin');
CREATE TYPE goal_role AS ENUM ('owner', 'moderator', 'member');
CREATE TYPE status    AS ENUM ('new', 'in_progress', 'done', 'cancelled');

CREATE TABLE users (
    user_id       INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    login         VARCHAR(100) NOT NULL UNIQUE,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    password_hash TEXT         NOT NULL,
    user_role     user_role    NOT NULL DEFAULT 'user',
    banned        BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE goal (
    goal_id      INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    description  TEXT,
    status       status       NOT NULL DEFAULT 'new',
    start_date   TIMESTAMPTZ,
    deadline     TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CHECK (start_date IS NULL OR deadline IS NULL OR start_date <= deadline)
);

CREATE TABLE task (
    task_id      INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    goal_id      INT NOT NULL REFERENCES goal (goal_id) ON DELETE CASCADE,
    author_id    INT REFERENCES users (user_id) ON DELETE SET NULL,
    name         VARCHAR(100) NOT NULL,
    description  TEXT,
    status       status       NOT NULL DEFAULT 'new',
    start_date   TIMESTAMPTZ,
    deadline     TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CHECK (start_date IS NULL OR deadline IS NULL OR start_date <= deadline)
);

CREATE TABLE user_goal (
    user_id   INT NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    goal_id   INT NOT NULL REFERENCES goal (goal_id)  ON DELETE CASCADE,
    goal_role goal_role NOT NULL DEFAULT 'member',
    PRIMARY KEY (user_id, goal_id)
);

-- У цели ровно один владелец
CREATE UNIQUE INDEX one_owner_per_goal ON user_goal (goal_id) WHERE goal_role = 'owner';

CREATE TABLE user_task (
    user_id INT NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    task_id INT NOT NULL REFERENCES task (task_id)  ON DELETE CASCADE,
    PRIMARY KEY (user_id, task_id)
);

CREATE TABLE auth_session (
    session_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id    INT NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    device_key TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at TIMESTAMPTZ
);

CREATE INDEX auth_session_user_id ON auth_session (user_id);

CREATE TABLE refresh_token (
    token_id   INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_id INT NOT NULL REFERENCES auth_session (session_id) ON DELETE CASCADE,
    token_hash CHAR(64)    NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    used_at    TIMESTAMPTZ
);

CREATE INDEX refresh_token_session_id ON refresh_token (session_id);