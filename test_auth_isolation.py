"""
Proves: Alice's token cannot be used to read Bob's ticket.
"""
import requests

BASE = "http://127.0.0.1:8000"


def _register_and_login(email: str, password: str = "testpass123") -> str:
    requests.post(f"{BASE}/register", json={"email": email, "password": password})
    r = requests.post(f"{BASE}/login", json={"email": email, "password": password})
    return r.json()["access_token"]


def test_alice_cannot_read_bobs_ticket():
    alice_token = _register_and_login("alice_test@example.com")
    bob_token = _register_and_login("bob_test@example.com")

    # Bob creates a ticket
    r = requests.post(
        f"{BASE}/tickets",
        json={"message": "Bob's private ticket about a late order."},
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert r.status_code == 201
    bob_ticket_id = r.json()["id"]

    # Alice tries to read Bob's ticket using her own valid token
    r = requests.get(
        f"{BASE}/tickets/{bob_ticket_id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert r.status_code == 404, "Alice should NOT be able to access Bob's ticket"


def test_alices_history_only_shows_her_own_tickets():
    alice_token = _register_and_login("alice_test2@example.com")
    bob_token = _register_and_login("bob_test2@example.com")

    requests.post(f"{BASE}/tickets", json={"message": "Bob ticket"},
                  headers={"Authorization": f"Bearer {bob_token}"})
    requests.post(f"{BASE}/tickets", json={"message": "Alice ticket"},
                  headers={"Authorization": f"Bearer {alice_token}"})

    r = requests.get(f"{BASE}/tickets", headers={"Authorization": f"Bearer {alice_token}"})
    messages = [t["message"] for t in r.json()]
    assert "Alice ticket" in messages
    assert "Bob ticket" not in messages
