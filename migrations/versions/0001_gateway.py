"""Immutable initial gateway schema and private-access hardening."""

from alembic import op

revision = "0001_gateway"
down_revision = None
branch_labels = None
depends_on = None

DDL = [
    """CREATE SCHEMA IF NOT EXISTS gateway""",
    """REVOKE ALL ON SCHEMA gateway FROM PUBLIC""",
    """SET LOCAL search_path TO gateway""",
    """CREATE TABLE users (
    id uuid PRIMARY KEY,
    username varchar(100) NOT NULL UNIQUE,
    password_hash text NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
)""",
    """CREATE TABLE conversations (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id),
    title varchar(160) NOT NULL DEFAULT 'New conversation',
    in_flight_request_id uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (id, user_id)
)""",
    """CREATE TABLE ai_requests (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id),
    conversation_id uuid,
    operation varchar(16) NOT NULL CHECK (operation IN ('chat', 'analyze')),
    route varchar(32) NOT NULL DEFAULT 'standard',
    requested_provider varchar(40) NOT NULL,
    requested_model varchar(120) NOT NULL,
    final_provider varchar(40),
    final_model varchar(120),
    status varchar(24) NOT NULL CHECK (
        status IN ('pending', 'succeeded', 'failed', 'timeout', 'refused',
            'rate_limited', 'cancelled')
    ),
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    latency_ms integer CHECK (latency_ms >= 0),
    http_status smallint CHECK (http_status BETWEEN 100 AND 599),
    input_tokens bigint CHECK (input_tokens >= 0),
    output_tokens bigint CHECK (output_tokens >= 0),
    token_usage_complete boolean NOT NULL DEFAULT false,
    attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    error_code varchar(80),
    structured_output jsonb,
    schema_version varchar(16),
    UNIQUE (id, conversation_id, user_id),
    FOREIGN KEY (conversation_id, user_id) REFERENCES conversations(id, user_id),
    CHECK ((operation = 'chat' AND conversation_id IS NOT NULL)
        OR (operation = 'analyze' AND conversation_id IS NULL)),
    CHECK ((status = 'pending' AND finished_at IS NULL AND latency_ms IS NULL)
        OR (status <> 'pending' AND finished_at IS NOT NULL AND latency_ms IS NOT NULL)),
    CHECK (structured_output IS NULL OR operation = 'analyze')
)""",
    """ALTER TABLE conversations ADD CONSTRAINT conversations_in_flight_fk
    FOREIGN KEY (in_flight_request_id, id, user_id)
    REFERENCES ai_requests(id, conversation_id, user_id)""",
    """CREATE TABLE messages (
    id uuid PRIMARY KEY,
    conversation_id uuid NOT NULL,
    user_id uuid NOT NULL,
    request_id uuid NOT NULL,
    sequence_number integer NOT NULL CHECK (sequence_number > 0),
    role varchar(16) NOT NULL CHECK (role IN ('user', 'assistant')),
    content text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (conversation_id, sequence_number),
    UNIQUE (request_id, role),
    FOREIGN KEY (conversation_id, user_id) REFERENCES conversations(id, user_id),
    FOREIGN KEY (request_id, conversation_id, user_id)
        REFERENCES ai_requests(id, conversation_id, user_id)
)""",
    """CREATE TABLE provider_attempts (
    id uuid PRIMARY KEY,
    request_id uuid NOT NULL REFERENCES ai_requests(id),
    attempt_number integer NOT NULL CHECK (attempt_number > 0),
    provider varchar(40) NOT NULL,
    requested_model varchar(120) NOT NULL,
    actual_model varchar(120),
    status varchar(24) NOT NULL CHECK (
        status IN ('started', 'succeeded', 'failed', 'timeout', 'refused',
            'incomplete', 'cancelled')
    ),
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    latency_ms integer CHECK (latency_ms >= 0),
    provider_request_id varchar(200),
    provider_response_id varchar(200),
    http_status smallint CHECK (http_status BETWEEN 100 AND 599),
    error_code varchar(80),
    input_tokens bigint CHECK (input_tokens >= 0),
    output_tokens bigint CHECK (output_tokens >= 0),
    usage_known boolean NOT NULL DEFAULT false,
    UNIQUE (request_id, attempt_number),
    CHECK ((status = 'started' AND finished_at IS NULL AND latency_ms IS NULL)
        OR (status <> 'started' AND finished_at IS NOT NULL AND latency_ms IS NOT NULL)),
    CHECK (NOT usage_known OR (input_tokens IS NOT NULL AND output_tokens IS NOT NULL))
)""",
    """CREATE TABLE rate_limit_buckets (
    scope varchar(40) NOT NULL,
    subject_hash varchar(100) NOT NULL,
    window_start timestamptz NOT NULL,
    window_seconds integer NOT NULL CHECK (window_seconds > 0),
    request_count integer NOT NULL CHECK (request_count >= 0),
    PRIMARY KEY (scope, subject_hash, window_start, window_seconds)
)""",
    """CREATE INDEX conversations_owner_order_idx ON conversations(user_id, updated_at DESC, id)""",
    """CREATE INDEX ai_requests_owner_time_idx ON ai_requests(user_id, started_at DESC)""",
    """CREATE INDEX ai_requests_pending_idx ON ai_requests(started_at) WHERE status = 'pending'""",
    """CREATE INDEX provider_attempts_request_idx ON provider_attempts(request_id)""",
    """CREATE INDEX rate_limit_expiry_idx ON rate_limit_buckets(window_start)""",
]


def upgrade():
    for statement in DDL:
        op.execute(statement)
    for role in ("anon", "authenticated"):
        op.execute(f"""DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{role}') THEN
                REVOKE ALL ON SCHEMA gateway FROM {role};
                REVOKE ALL ON ALL TABLES IN SCHEMA gateway FROM {role};
                REVOKE ALL ON ALL SEQUENCES IN SCHEMA gateway FROM {role};
                ALTER DEFAULT PRIVILEGES IN SCHEMA gateway REVOKE ALL ON TABLES FROM {role};
            END IF;
        END $$""")
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA gateway FROM PUBLIC")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA gateway REVOKE ALL ON TABLES FROM PUBLIC")
    for table in (
        "users",
        "conversations",
        "ai_requests",
        "messages",
        "provider_attempts",
        "rate_limit_buckets",
    ):
        op.execute(f"ALTER TABLE gateway.{table} ENABLE ROW LEVEL SECURITY")


def downgrade():
    # No automated destructive rollback against a shared managed database.
    raise RuntimeError("Initial schema downgrade requires an explicit backup and removal plan")
