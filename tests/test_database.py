import pytest
from database import init_db, get_user, create_or_update_user

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield
    import os
    if os.path.exists("users.db"):
        os.remove("users.db")

def test_create_user():
    create_or_update_user(1, "12345")
    user = get_user(1)
    assert user == (1, 1, "12345")

def test_update_user():
    create_or_update_user(1, "12345")
    create_or_update_user(1, "67890")
    user = get_user(1)
    assert user == (2, 1, "67890")