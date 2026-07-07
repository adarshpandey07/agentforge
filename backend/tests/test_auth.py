"""Auth flow tests: register, login, me, bad credentials."""
from tests.conftest import register_and_login


async def test_register_login_me(client):
    headers = await register_and_login(client)

    # duplicate email rejected
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": "Other",
            "email": "owner@acme-corp.com",
            "password": "supersecret123",
        },
    )
    assert resp.status_code == 409

    # login works
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "owner@acme-corp.com", "password": "supersecret123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["user"]["role"] == "owner"

    # me returns the authenticated user
    resp = await client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "owner@acme-corp.com"


async def test_login_bad_password(client):
    await register_and_login(client)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "owner@acme-corp.com", "password": "wrong-password"},
    )
    assert resp.status_code == 401


async def test_me_requires_token(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
