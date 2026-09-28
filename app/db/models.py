"""Schema-qualified ORM models. Alembic, rather than create_all, owns deployment DDL."""

from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    MetaData,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, mapped_column


class Base(DeclarativeBase):
    metadata = MetaData(schema="gateway")


class User(Base):
    __tablename__ = "users"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = mapped_column(String(100), nullable=False, unique=True)
    password_hash = mapped_column(Text, nullable=False)
    is_active = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class Conversation(Base):
    __tablename__ = "conversations"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = mapped_column(UUID(as_uuid=True), ForeignKey("gateway.users.id"), nullable=False)
    title = mapped_column(String(160), nullable=False, server_default=text("'New conversation'"))
    in_flight_request_id = mapped_column(UUID(as_uuid=True))
    created_at = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    __table_args__ = (
        UniqueConstraint("id", "user_id"),
        ForeignKeyConstraint(
            ["in_flight_request_id", "id", "user_id"],
            [
                "gateway.ai_requests.id",
                "gateway.ai_requests.conversation_id",
                "gateway.ai_requests.user_id",
            ],
            name="conversations_in_flight_fk",
            use_alter=True,
        ),
        Index("conversations_owner_order_idx", "user_id", text("updated_at DESC"), "id"),
    )


class AIRequest(Base):
    __tablename__ = "ai_requests"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = mapped_column(UUID(as_uuid=True), ForeignKey("gateway.users.id"), nullable=False)
    conversation_id = mapped_column(UUID(as_uuid=True))
    operation = mapped_column(String(16), nullable=False)
    route = mapped_column(String(32), nullable=False, server_default=text("'standard'"))
    requested_provider = mapped_column(String(40), nullable=False)
    requested_model = mapped_column(String(120), nullable=False)
    final_provider = mapped_column(String(40))
    final_model = mapped_column(String(120))
    status = mapped_column(String(24), nullable=False)
    started_at = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    finished_at = mapped_column(DateTime(timezone=True))
    latency_ms = mapped_column(Integer)
    http_status = mapped_column(SmallInteger)
    input_tokens = mapped_column(BigInteger)
    output_tokens = mapped_column(BigInteger)
    token_usage_complete = mapped_column(Boolean, nullable=False, server_default=text("false"))
    attempt_count = mapped_column(Integer, nullable=False, server_default=text("0"))
    error_code = mapped_column(String(80))
    structured_output = mapped_column(JSONB)
    schema_version = mapped_column(String(16))
    __table_args__ = (
        UniqueConstraint("id", "conversation_id", "user_id"),
        ForeignKeyConstraint(
            ["conversation_id", "user_id"],
            ["gateway.conversations.id", "gateway.conversations.user_id"],
        ),
        CheckConstraint("operation IN ('chat', 'analyze')"),
        CheckConstraint(
            "status IN ('pending','succeeded','failed','timeout','refused','rate_limited',"
            "'cancelled')"
        ),
        CheckConstraint("latency_ms >= 0"),
        CheckConstraint("http_status BETWEEN 100 AND 599"),
        CheckConstraint("input_tokens >= 0"),
        CheckConstraint("output_tokens >= 0"),
        CheckConstraint("attempt_count >= 0"),
        CheckConstraint(
            "(operation='chat' AND conversation_id IS NOT NULL) OR (operation='analyze'"
            " AND conversation_id IS NULL)"
        ),
        CheckConstraint(
            "(status='pending' AND finished_at IS NULL AND latency_ms IS NULL) OR"
            " (status<>'pending' AND finished_at IS NOT NULL AND latency_ms IS NOT NULL)"
        ),
        CheckConstraint("structured_output IS NULL OR operation='analyze'"),
        Index("ai_requests_owner_time_idx", "user_id", text("started_at DESC")),
        Index("ai_requests_pending_idx", "started_at", postgresql_where=text("status='pending'")),
    )


class Message(Base):
    __tablename__ = "messages"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id = mapped_column(UUID(as_uuid=True), nullable=False)
    request_id = mapped_column(UUID(as_uuid=True), nullable=False)
    sequence_number = mapped_column(Integer, nullable=False)
    role = mapped_column(String(16), nullable=False)
    content = mapped_column(Text, nullable=False)
    created_at = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    __table_args__ = (
        UniqueConstraint("conversation_id", "sequence_number"),
        UniqueConstraint("request_id", "role"),
        ForeignKeyConstraint(
            ["conversation_id", "user_id"],
            ["gateway.conversations.id", "gateway.conversations.user_id"],
        ),
        ForeignKeyConstraint(
            ["request_id", "conversation_id", "user_id"],
            [
                "gateway.ai_requests.id",
                "gateway.ai_requests.conversation_id",
                "gateway.ai_requests.user_id",
            ],
        ),
        CheckConstraint("sequence_number > 0"),
        CheckConstraint("role IN ('user','assistant')"),
    )


class ProviderAttempt(Base):
    __tablename__ = "provider_attempts"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    request_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("gateway.ai_requests.id"), nullable=False
    )
    attempt_number = mapped_column(Integer, nullable=False)
    provider = mapped_column(String(40), nullable=False)
    requested_model = mapped_column(String(120), nullable=False)
    actual_model = mapped_column(String(120))
    status = mapped_column(String(24), nullable=False)
    started_at = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    finished_at = mapped_column(DateTime(timezone=True))
    latency_ms = mapped_column(Integer)
    provider_request_id = mapped_column(String(200))
    provider_response_id = mapped_column(String(200))
    http_status = mapped_column(SmallInteger)
    error_code = mapped_column(String(80))
    input_tokens = mapped_column(BigInteger)
    output_tokens = mapped_column(BigInteger)
    usage_known = mapped_column(Boolean, nullable=False, server_default=text("false"))
    __table_args__ = (
        UniqueConstraint("request_id", "attempt_number"),
        CheckConstraint("attempt_number > 0"),
        CheckConstraint(
            "status IN ('started','succeeded','failed','timeout','refused','incomplete',"
            "'cancelled')"
        ),
        CheckConstraint("latency_ms >= 0"),
        CheckConstraint("http_status BETWEEN 100 AND 599"),
        CheckConstraint("input_tokens >= 0"),
        CheckConstraint("output_tokens >= 0"),
        CheckConstraint(
            "(status='started' AND finished_at IS NULL AND latency_ms IS NULL) OR"
            " (status<>'started' AND finished_at IS NOT NULL AND latency_ms IS NOT NULL)"
        ),
        CheckConstraint(
            "NOT usage_known OR (input_tokens IS NOT NULL AND output_tokens IS NOT NULL)"
        ),
        Index("provider_attempts_request_idx", "request_id"),
    )


class RateLimitBucket(Base):
    __tablename__ = "rate_limit_buckets"
    scope = mapped_column(String(40), primary_key=True)
    subject_hash = mapped_column(String(100), primary_key=True)
    window_start = mapped_column(DateTime(timezone=True), primary_key=True)
    window_seconds = mapped_column(Integer, primary_key=True)
    request_count = mapped_column(Integer, nullable=False)
    __table_args__ = (
        CheckConstraint("window_seconds > 0"),
        CheckConstraint("request_count >= 0"),
        Index("rate_limit_expiry_idx", "window_start"),
    )
