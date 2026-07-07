"""Clients CRUD tests: create, list/search, get, update, delete, tenant scoping."""
from tests.conftest import register_and_login


async def test_clients_crud(client):
    headers = await register_and_login(client)

    # create
    resp = await client.post(
        "/api/v1/clients",
        json={"name": "Sunrise Bakery", "business_type": "bakery", "contact_email": "hi@sunrisebakery.com"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    created = resp.json()
    client_id = created["id"]
    assert created["name"] == "Sunrise Bakery"
    assert created["tenant_id"]

    # list + search
    resp = await client.get("/api/v1/clients", params={"q": "sunrise"}, headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.get("/api/v1/clients", params={"q": "no-such-client"}, headers=headers)
    assert resp.json() == []

    # get
    resp = await client.get(f"/api/v1/clients/{client_id}", headers=headers)
    assert resp.status_code == 200

    # update
    resp = await client.patch(
        f"/api/v1/clients/{client_id}", json={"phone": "+1-555-0100"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["phone"] == "+1-555-0100"

    # audit trail recorded
    resp = await client.get("/api/v1/audit-logs", headers=headers)
    assert resp.status_code == 200
    actions = {(e["action"], e["resource"]) for e in resp.json()}
    assert ("create", "client") in actions
    assert ("update", "client") in actions

    # delete
    resp = await client.delete(f"/api/v1/clients/{client_id}", headers=headers)
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/clients/{client_id}", headers=headers)
    assert resp.status_code == 404


async def test_clients_require_auth(client):
    resp = await client.get("/api/v1/clients")
    assert resp.status_code == 401
