from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    __table_args__ = (
        db.CheckConstraint(
            "role IN ('user', 'admin')",
            name="ck_users_role",
        ),
        db.CheckConstraint(
            "status IN ('active', 'dormant')",
            name="ck_users_status",
        ),
        db.CheckConstraint(
            "balance >= 0",
            name="ck_users_balance_nonnegative",
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    username = db.Column(
        db.String(24, collation="NOCASE"),
        unique=True,
        nullable=False,
        index=True,
    )

    display_name = db.Column(
        db.String(40),
        nullable=False,
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False,
    )

    bio = db.Column(
        db.String(300),
        nullable=False,
        default="",
    )

    role = db.Column(
        db.String(10),
        nullable=False,
        default="user",
    )

    status = db.Column(
        db.String(10),
        nullable=False,
        default="active",
    )

    balance = db.Column(
        db.Integer,
        nullable=False,
        default=100_000,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    products = db.relationship(
        "Product",
        back_populates="seller",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # 이 사용자가 작성한 신고 목록
    reports_made = db.relationship(
        "Report",
        foreign_keys="Report.reporter_id",
        back_populates="reporter",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # 이 사용자를 대상으로 작성된 신고 목록
    reports_received = db.relationship(
        "Report",
        foreign_keys="Report.target_user_id",
        back_populates="target_user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    transfers_sent = db.relationship(
        "Transfer",
        foreign_keys="Transfer.sender_id",
        back_populates="sender",
        lazy="select",
    )

    transfers_received = db.relationship(
        "Transfer",
        foreign_keys="Transfer.recipient_id",
        back_populates="recipient",
        lazy="select",
    )
    chat_messages_sent = db.relationship(
        "ChatMessage",
        foreign_keys="ChatMessage.sender_id",
        back_populates="sender",
        cascade="all, delete-orphan",
        lazy="select",
    )

    chat_messages_received = db.relationship(
        "ChatMessage",
        foreign_keys="ChatMessage.recipient_id",
        back_populates="recipient",
        lazy="select",
    )

    def set_password(self, password):
        """비밀번호 원문 대신 scrypt 해시를 저장한다."""
        if not isinstance(password, str):
            raise TypeError("비밀번호는 문자열이어야 합니다.")

        if not 10 <= len(password) <= 128:
            raise ValueError(
                "비밀번호는 10자 이상 128자 이하여야 합니다."
            )

        self.password_hash = generate_password_hash(
            password,
            method="scrypt",
        )

    def check_password(self, password):
        """입력한 비밀번호가 저장된 해시와 일치하는지 확인한다."""
        if not isinstance(password, str):
            return False

        return check_password_hash(
            self.password_hash,
            password,
        )

    @property
    def is_active(self):
        return self.status == "active"

    @property
    def is_admin(self):
        return self.role == "admin"

    def __repr__(self):
        return f"<User id={self.id} username={self.username!r}>"


class Product(db.Model):
    __tablename__ = "products"

    __table_args__ = (
        db.CheckConstraint(
            "price BETWEEN 0 AND 100000000",
            name="ck_products_price_range",
        ),
        db.CheckConstraint(
            "status IN ('available', 'reserved', 'sold', 'blocked')",
            name="ck_products_status",
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    seller_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name = db.Column(
        db.String(100),
        nullable=False,
        index=True,
    )

    description = db.Column(
        db.String(1000),
        nullable=False,
    )

    price = db.Column(
        db.Integer,
        nullable=False,
    )

    image_filename = db.Column(
        db.String(255),
        nullable=False,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="available",
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    seller = db.relationship(
        "User",
        back_populates="products",
    )

    # 이 상품을 대상으로 작성된 신고 목록
    reports_received = db.relationship(
        "Report",
        foreign_keys="Report.target_product_id",
        back_populates="target_product",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return f"<Product id={self.id} name={self.name!r}>"


class Report(db.Model):
    __tablename__ = "reports"

    __table_args__ = (
        # 사용자 또는 상품 중 정확히 하나만 신고 대상으로 지정한다.
        db.CheckConstraint(
            """
            (
                target_user_id IS NOT NULL
                AND target_product_id IS NULL
            )
            OR
            (
                target_user_id IS NULL
                AND target_product_id IS NOT NULL
            )
            """,
            name="ck_reports_exactly_one_target",
        ),
        # 같은 사용자가 같은 사용자를 중복 신고하지 못하게 한다.
        db.UniqueConstraint(
            "reporter_id",
            "target_user_id",
            name="uq_reports_reporter_user",
        ),
        # 같은 사용자가 같은 상품을 중복 신고하지 못하게 한다.
        db.UniqueConstraint(
            "reporter_id",
            "target_product_id",
            name="uq_reports_reporter_product",
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    reporter_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    target_user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    target_product_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "products.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    reason = db.Column(
        db.String(500),
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    reporter = db.relationship(
        "User",
        foreign_keys=[reporter_id],
        back_populates="reports_made",
    )

    target_user = db.relationship(
        "User",
        foreign_keys=[target_user_id],
        back_populates="reports_received",
    )

    target_product = db.relationship(
        "Product",
        foreign_keys=[target_product_id],
        back_populates="reports_received",
    )

    @property
    def target_type(self):
        if self.target_user_id is not None:
            return "user"

        return "product"

    def __repr__(self):
        return (
            f"<Report id={self.id} "
            f"target_type={self.target_type!r}>"
        )
    
class Transfer(db.Model):
    __tablename__ = "transfers"

    __table_args__ = (
        db.CheckConstraint(
            "amount BETWEEN 1 AND 1000000",
            name="ck_transfers_amount_range",
        ),
        db.CheckConstraint(
            "sender_id != recipient_id",
            name="ck_transfers_different_users",
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    recipient_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    amount = db.Column(
        db.Integer,
        nullable=False,
    )

    memo = db.Column(
        db.String(100),
        nullable=False,
        default="",
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    sender = db.relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="transfers_sent",
    )

    recipient = db.relationship(
        "User",
        foreign_keys=[recipient_id],
        back_populates="transfers_received",
    )

    def __repr__(self):
        return (
            f"<Transfer id={self.id} "
            f"sender_id={self.sender_id} "
            f"recipient_id={self.recipient_id} "
            f"amount={self.amount}>"
        )    
class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    __table_args__ = (
        db.CheckConstraint(
            "scope IN ('public', 'direct')",
            name="ck_chat_messages_scope",
        ),
        db.CheckConstraint(
            "("
            "scope = 'public' AND recipient_id IS NULL"
            ") OR ("
            "scope = 'direct' "
            "AND recipient_id IS NOT NULL "
            "AND sender_id != recipient_id"
            ")",
            name="ck_chat_messages_target",
        ),
        db.CheckConstraint(
            "length(content) BETWEEN 1 AND 500",
            name="ck_chat_messages_content_length",
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    recipient_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    scope = db.Column(
        db.String(10),
        nullable=False,
    )

    content = db.Column(
        db.String(500),
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    sender = db.relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="chat_messages_sent",
    )

    recipient = db.relationship(
        "User",
        foreign_keys=[recipient_id],
        back_populates="chat_messages_received",
    )

    def __repr__(self):
        return (
            f"<ChatMessage id={self.id} "
            f"scope={self.scope!r} "
            f"sender_id={self.sender_id}>"
        )