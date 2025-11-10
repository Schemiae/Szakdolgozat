import unittest
from unittest.mock import patch
from flask_app.services import user_service
from db_fakes import FakeConnection

class TestUserService(unittest.TestCase):
    def test_create_user(self):
        steps = [{
            "expect": "INSERT INTO users",
            "params": ("alice", "hashed-secret", False),
            "fetch": "one",
            "result": {"username": "alice", "is_admin": False},
        }]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(user_service, 'get_connection', return_value=fake_conn), \
             patch.object(user_service.bcrypt, 'generate_password_hash', return_value=b"hashed-secret"):
            res = user_service.create_user("alice", "secret")
        self.assertEqual(res, {"username": "alice", "is_admin": False})
        q = fake_conn.cursor().queries[0]
        self.assertIn("INSERT INTO users", q)
        self.assertIn("RETURNING username, is_admin", q)
        self.assertEqual(fake_conn.cursor().params_list[0], ("alice", "hashed-secret", False))
        self.assertTrue(fake_conn.commit_called)

    def test_get_user_by_username(self):
        # Létező felhasználó
        row = {
            "username": "bob",
            "password": "pw-hash",
            "is_admin": True,
            "balance": 12345
        }
        steps = [{
            "expect": "FROM users",
            "params": ("bob",),
            "fetch": "one",
            "result": row,
        }]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(user_service, 'get_connection', return_value=fake_conn):
            res = user_service.get_user_by_username("bob")
        self.assertEqual(res, row)
        q = fake_conn.cursor().queries[0]
        self.assertIn("SELECT username, password, is_admin, balance FROM users WHERE username = %s", q)
        self.assertEqual(fake_conn.cursor().params_list[0], ("bob",))
        self.assertFalse(fake_conn.commit_called)

        # Nem létező felhasználó
        steps = [{
            "expect": "WHERE username = %s",
            "params": ("ghost",),
            "fetch": "one",
            "result": None,
        }]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(user_service, 'get_connection', return_value=fake_conn):
            res = user_service.get_user_by_username("ghost")
        self.assertIsNone(res)
        self.assertFalse(fake_conn.commit_called)

if __name__ == "__main__":
    unittest.main()
