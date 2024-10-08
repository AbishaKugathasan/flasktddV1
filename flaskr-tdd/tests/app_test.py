import os
import json
import pytest
from pathlib import Path

from project.app import app, db, login_required

TEST_DB = "test.db"

@pytest.fixture
@app.route("/loginHelper")
@login_required
def testLoginRequiredHelper(): 
    return "logged in"

@pytest.fixture
def client():
    BASE_DIR = Path(__file__).resolve().parent.parent
    app.config["TESTING"] = True
    app.config["DATABASE"] = BASE_DIR.joinpath(TEST_DB)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR.joinpath(TEST_DB)}"

    with app.app_context():
        db.create_all()  # setup
        yield app.test_client()  # tests run here
        db.drop_all()  # teardown


def login(client, username, password):
    """Login helper function"""
    return client.post(
        "/login",
        data=dict(username=username, password=password),
        follow_redirects=True,
    )


def logout(client):
    """Logout helper function"""
    return client.get("/logout", follow_redirects=True)


def test_index(client):
    response = client.get("/", content_type="html/text")
    assert response.status_code == 200


def test_database(client):
    """initial test. ensure that the database exists"""
    tester = Path("test.db").is_file()
    assert tester


def test_empty_db(client):
    """Ensure database is blank"""
    rv = client.get("/")
    assert b"No entries yet. Add some!" in rv.data


def test_login_logout(client):
    """Test login and logout using helper functions"""
    rv = login(client, app.config["USERNAME"], app.config["PASSWORD"])
    assert b"You were logged in" in rv.data
    rv = logout(client)
    assert b"You were logged out" in rv.data
    rv = login(client, app.config["USERNAME"] + "x", app.config["PASSWORD"])
    assert b"Invalid username" in rv.data
    rv = login(client, app.config["USERNAME"], app.config["PASSWORD"] + "x")
    assert b"Invalid password" in rv.data


def test_messages(client):
    """Ensure that user can post messages"""
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    rv = client.post(
        "/add",
        data=dict(title="<Hello>", text="<strong>HTML</strong> allowed here"),
        follow_redirects=True,
    )
    assert b"No entries here so far" not in rv.data
    assert b"&lt;Hello&gt;" in rv.data
    assert b"<strong>HTML</strong> allowed here" in rv.data

def test_delete_message(client):
    """Ensure the messages are being deleted"""
    rv = client.get('/delete/1')
    data = json.loads(rv.data)
    assert data["status"] == 1

# Test #1 for /search/
def testWithQuery(client):
    """Checks that search works with a query."""
    login(client, app.config["USERNAME"], app.config["PASSWORD"])

    rv = client.post(
        "/add",
        data=dict(title="Example Post", text="Fake Content"),
        follow_redirects=True,
    )
    assert b"New entry was successfully posted" in rv.data  # Confirm post was added

    rv = client.get(
        "/search/?query=Example",
        follow_redirects=True,
    )

    assert b"Example Post" in rv.data
    assert b"Fake Content" in rv.data
    assert rv.status_code == 200

# Test #2 for /search/
def testWithoutQuery(client):
    """Checks that search does not work with a query."""

    login(client, app.config["USERNAME"], app.config["PASSWORD"])

    rv = client.get(
        "/search/",
        follow_redirects=True,
    )
    assert b"Example Post" not in rv.data 

# Test #3 for login_required 
def testLoginRequired(client):
    """Check if login is required"""
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    res = client.get("/loginHelper")
    assert res.status_code == 200  
    assert b'logged in' in res.data

# Test #4 login_not_required
def testLoginRequiredNot(client):
    """Check if login is required"""
    res = client.get("/loginHelper")
    assert res.status_code == 401  
    assert b'message' in res.data
