from app.extensions import db
from app.models import ChatMessage, Transfer, User


def create_user(
    app,
    username,
    display_name,
    password="SecurePass123!",
    role="user",
    status="active",
    balance=100_000,
):
    with app.app_context():
        user = User(
            username=username,
            display_name=display_name,
            role=role,
            status=status,
            balance=balance,
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return user.id


def login_as(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_password_is_hashed(app):
    user_id = create_user(
        app,
        username="secure_user",
        display_name="보안 사용자",
    )

    with app.app_context():
        user = db.session.get(User, user_id)

        assert user.password_hash != "SecurePass123!"
        assert user.check_password("SecurePass123!")
        assert not user.check_password("WrongPass123!")


def test_admin_page_rejects_normal_user(app, client):
    normal_user_id = create_user(
        app,
        username="normal_user",
        display_name="일반 사용자",
    )

    login_as(client, normal_user_id)

    response = client.get("/admin/")

    assert response.status_code == 403


def test_admin_page_allows_admin(app, client):
    admin_id = create_user(
        app,
        username="admin_user",
        display_name="관리자",
        role="admin",
    )

    login_as(client, admin_id)

    response = client.get("/admin/")

    assert response.status_code == 200
    assert "관리자 센터".encode() in response.data


def test_secure_transfer_updates_both_balances(app, client):
    sender_id = create_user(
        app,
        username="sender",
        display_name="보내는 사용자",
        balance=100_000,
    )

    recipient_id = create_user(
        app,
        username="recipient",
        display_name="받는 사용자",
        balance=100_000,
    )

    login_as(client, sender_id)

    response = client.post(
        "/transfers/new",
        data={
            "recipient_username": "recipient",
            "amount": 25_000,
            "memo": "테스트 송금",
        },
    )

    assert response.status_code == 302

    with app.app_context():
        sender = db.session.get(User, sender_id)
        recipient = db.session.get(User, recipient_id)

        transfer_count = db.session.scalar(
            db.select(db.func.count(Transfer.id))
        )

        assert sender.balance == 75_000
        assert recipient.balance == 125_000
        assert transfer_count == 1


def test_transfer_rejects_insufficient_balance(app, client):
    sender_id = create_user(
        app,
        username="poor_sender",
        display_name="잔액 부족 사용자",
        balance=1_000,
    )

    recipient_id = create_user(
        app,
        username="rich_recipient",
        display_name="받는 사용자",
        balance=100_000,
    )

    login_as(client, sender_id)

    response = client.post(
        "/transfers/new",
        data={
            "recipient_username": "rich_recipient",
            "amount": 10_000,
            "memo": "",
        },
    )

    assert response.status_code == 200

    with app.app_context():
        sender = db.session.get(User, sender_id)
        recipient = db.session.get(User, recipient_id)

        transfer_count = db.session.scalar(
            db.select(db.func.count(Transfer.id))
        )

        assert sender.balance == 1_000
        assert recipient.balance == 100_000
        assert transfer_count == 0


def test_transfer_rejects_self_transfer(app, client):
    user_id = create_user(
        app,
        username="self_user",
        display_name="자기 송금 사용자",
    )

    login_as(client, user_id)

    response = client.post(
        "/transfers/new",
        data={
            "recipient_username": "self_user",
            "amount": 1_000,
            "memo": "",
        },
    )

    assert response.status_code == 200

    with app.app_context():
        user = db.session.get(User, user_id)

        transfer_count = db.session.scalar(
            db.select(db.func.count(Transfer.id))
        )

        assert user.balance == 100_000
        assert transfer_count == 0


def test_chat_escapes_script_content(app, client):
    user_id = create_user(
        app,
        username="chat_user",
        display_name="채팅 사용자",
    )

    login_as(client, user_id)

    response = client.post(
        "/chat/public",
        data={
            "content": "<script>alert(1)</script>",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"<script>alert(1)</script>" not in response.data
    assert b"&lt;script&gt;alert(1)&lt;/script&gt;" in response.data

    with app.app_context():
        message_count = db.session.scalar(
            db.select(db.func.count(ChatMessage.id))
        )

        assert message_count == 1