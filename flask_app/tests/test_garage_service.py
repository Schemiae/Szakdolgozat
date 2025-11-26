import unittest
from unittest.mock import patch
from services import garage_service
from db_fakes import FakeConnection

class TestGarageService(unittest.TestCase):
    def test_list_garages_for_user(self):
        rows = [
            {"id": 1, "name": "Main", "unlocked": True},
            {"id": 2, "name": "Secondary", "unlocked": False},
        ]
        steps = [
            {"expect": "FROM garages", "params": ("alice",), "fetch": "all", "result": rows}
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(garage_service, 'get_connection', return_value=fake_conn):
            result = garage_service.list_garages_for_user("alice")
        self.assertEqual(len(result), 2)
        self.assertTrue(result[0]["unlocked"])
        self.assertFalse(result[1]["unlocked"])
        executed = " ".join(fake_conn.cursor().queries[0].split())
        self.assertIn("LEFT JOIN user_garages", executed)
        self.assertEqual(fake_conn.cursor().params_list[0], ("alice",))
        self.assertFalse(fake_conn.commit_called)

    def test_unlock_garage(self):
        # Garázs már fel van oldva
        steps = [
            {
                "expect": "SELECT 1 FROM user_garages",
                "params": ("alice", 3),
                "fetch": "one",
                "result": {"dummy": 1},
            }
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(garage_service, 'get_connection', return_value=fake_conn):
            res, status = garage_service.unlock_garage_for_user("alice", 3)
        self.assertEqual(status, 400)
        self.assertIn("already unlocked", res["error"])
        self.assertFalse(fake_conn.commit_called)
        self.assertIn("SELECT 1 FROM user_garages", fake_conn.cursor().queries[0])

        # Garázs ingyenes feloldása
        steps = [
            {
                "expect": "SELECT 1 FROM user_garages",
                "params": ("alice", 1),
                "fetch": "one",
                "result": None,
            },
            {
                "expect": "SELECT COUNT(*) AS cnt FROM user_garages",
                "params": ("alice",),
                "fetch": "one",
                "result": {"cnt": 0},
            },
            {
                "expect": "INSERT INTO user_garages",
                "params": ("alice", 1),
                "fetch": None,
                "result": None,
            },
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(garage_service, 'get_connection', return_value=fake_conn):
            res = garage_service.unlock_garage_for_user("alice", 1)
        self.assertEqual(res["message"], "Garage unlocked")
        self.assertTrue(fake_conn.commit_called)
        queries = fake_conn.cursor().queries
        self.assertIn("SELECT 1 FROM user_garages", queries[0])
        self.assertIn("SELECT COUNT(*) AS cnt FROM user_garages", queries[1])
        self.assertIn("INSERT INTO user_garages", queries[-1])

        # Garázs feloldása
        steps = [
            {
                "expect": "SELECT 1 FROM user_garages",
                "params": ("alice", 2),
                "fetch": "one",
                "result": None,
            },
            {
                "expect": "SELECT COUNT(*) AS cnt FROM user_garages",
                "params": ("alice",),
                "fetch": "one",
                "result": {"cnt": 1},
            },
            {
                "expect": "SELECT balance FROM users",
                "params": ("alice",),
                "fetch": "one",
                "result": {"balance": 200000},
            },
            {
                "expect": "UPDATE users SET balance = balance -",
                "params": (100000, "alice"),
                "fetch": None,
                "result": None,
            },
            {
                "expect": "INSERT INTO user_garages",
                "params": ("alice", 2),
                "fetch": None,
                "result": None,
            },
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(garage_service, 'get_connection', return_value=fake_conn):
            res = garage_service.unlock_garage_for_user("alice", 2)
        self.assertEqual(res["message"], "Garage unlocked")
        self.assertTrue(fake_conn.commit_called)
        q = fake_conn.cursor().queries
        self.assertIn("SELECT balance FROM users", " ".join(q[2].split()))
        self.assertTrue(any("UPDATE users SET balance = balance -" in x for x in q))
        self.assertTrue(any("INSERT INTO user_garages" in x for x in q))

        # Garázs sikertelen feloldása (nem elegendő egyenleg)
        steps = [
            {
                "expect": "SELECT 1 FROM user_garages",
                "params": ("alice", 3),
                "fetch": "one",
                "result": None,
            },
            {
                "expect": "SELECT COUNT(*) AS cnt FROM user_garages",
                "params": ("alice",),
                "fetch": "one",
                "result": {"cnt": 1},
            },
            {
                "expect": "SELECT balance FROM users",
                "params": ("alice",),
                "fetch": "one",
                "result": {"balance": 50000},
            },
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(garage_service, 'get_connection', return_value=fake_conn):
            res, status = garage_service.unlock_garage_for_user("alice", 3)
        self.assertEqual(status, 400)
        self.assertIn("Insufficient balance", res["error"])
        self.assertFalse(fake_conn.commit_called)
        q = fake_conn.cursor().queries
        self.assertIn("SELECT balance FROM users", " ".join(q[2].split()))
        self.assertFalse(any("INSERT INTO user_garages" in x for x in q))

if __name__ == "__main__":
    unittest.main()
