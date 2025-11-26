import unittest
from unittest.mock import patch
from services import line_service
from db_fakes import FakeConnection

class TestLineService(unittest.TestCase):
    def test_list_lines(self):
        rows = [
            {"name": "10", "provider_garage_id": 1, "travel_time_garage": 12, "travel_time_line": 30},
            {"name": "12A", "provider_garage_id": 2, "travel_time_garage": 8, "travel_time_line": 25},
        ]
        steps = [{
            "expect": "FROM lines",
            "params": None,
            "fetch": "all",
            "result": rows,
        }]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(line_service, 'get_connection', return_value=fake_conn):
            res = line_service.list_lines()
        self.assertEqual(res, rows)
        q = fake_conn.cursor().queries[0]
        self.assertIn("SELECT name, provider_garage_id, travel_time_garage, travel_time_line", q)
        self.assertIn("FROM lines", q)
        self.assertIn("ORDER BY name", q)
        self.assertIsNone(fake_conn.cursor().params_list[0])
        self.assertFalse(fake_conn.commit_called)

    def test_get_line(self):
        # Létező vonal lekérdezése
        row = {"name": "12A", "provider_garage_id": 2, "travel_time_garage": 8, "travel_time_line": 25}
        steps = [{
            "expect": "FROM lines",
            "params": ("12A",),
            "fetch": "one",
            "result": row,
        }]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(line_service, 'get_connection', return_value=fake_conn):
            res = line_service.get_line("12A")
        self.assertEqual(res, row)
        q = fake_conn.cursor().queries[0]
        self.assertIn("WHERE name = %s", q)
        self.assertEqual(fake_conn.cursor().params_list[0], ("12A",))
        self.assertFalse(fake_conn.commit_called)

        # Nem létező vonal lekérdezése
        steps = [{
            "expect": "WHERE name = %s",
            "params": ("ZZZ",),
            "fetch": "one",
            "result": None,
        }]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(line_service, 'get_connection', return_value=fake_conn):
            res = line_service.get_line("ZZZ")
        self.assertIsNone(res)
        self.assertFalse(fake_conn.commit_called)

if __name__ == "__main__":
    unittest.main()
