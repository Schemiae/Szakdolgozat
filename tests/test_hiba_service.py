import unittest
from unittest.mock import patch
from flask_app.services import hiba_service
from db_fakes import FakeConnection

class TestHibaService(unittest.TestCase):
    def test_list_issues_by_bus(self):
        rows = [
            {"id": 1, "bus": "AAA-111", "time": "2024-01-01 10:00:00", "repair_time": "2024-01-02 10:00:00", "repair_cost": 1000, "description": "desc1"},
            {"id": 2, "bus": "AAA-111", "time": "2024-01-03 11:00:00", "repair_time": "2024-01-04 11:00:00", "repair_cost": 2000, "description": "desc2"},
        ]
        steps = [{
            "expect": "FROM issues WHERE bus = %s",
            "params": ("AAA-111",),
            "fetch": "all",
            "result": rows,
        }]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(hiba_service, 'get_connection', return_value=fake_conn):
            res = hiba_service.list_issues_by_bus("AAA-111")
        self.assertEqual(len(res), 2)
        self.assertIn("SELECT * FROM issues", fake_conn.cursor().queries[0])
        self.assertEqual(fake_conn.cursor().params_list[0], ("AAA-111",))
        self.assertIsInstance(res[0]["time"], str)
        self.assertIsInstance(res[0]["repair_time"], str)

    def test_list_issues_for_user(self):
        buses = [{"plate": "AAA-111"}, {"plate": "BBB-222"}]
        steps = [
            {
                "expect": "FROM issues WHERE bus = %s",
                "params": ("AAA-111",),
                "fetch": "all",
                "result": [{"id": 1, "bus": "AAA-111", "time": "x", "repair_time": "y", "repair_cost": 100, "description": "a"}],
            },
            {
                "expect": "FROM issues WHERE bus = %s",
                "params": ("BBB-222",),
                "fetch": "all",
                "result": [
                    {"id": 2, "bus": "BBB-222", "time": "x2", "repair_time": "y2", "repair_cost": 200, "description": "b"},
                    {"id": 3, "bus": "BBB-222", "time": "x3", "repair_time": "y3", "repair_cost": 300, "description": "c"},
                ],
            },
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(hiba_service, 'get_connection', return_value=fake_conn):
            with patch.object(hiba_service, 'get_buses_for_user', return_value=buses):
                res = hiba_service.list_issues_for_user("alice", False)
        self.assertEqual(len(res), 3)
        q = fake_conn.cursor().queries
        self.assertIn("FROM issues WHERE bus = %s", q[0])
        self.assertIn("FROM issues WHERE bus = %s", q[1])

    def test_create_issue(self):
        data = {
            "bus": "AAA-111",
            "time": "2024-01-01 10:00:00",
            "repair_time": "2024-01-02 10:00:00",
            "repair_cost": 1500,
            "description": "brake issue",
        }
        steps = [
            {
                "expect": "INSERT INTO issues",
                "params": ("AAA-111", "2024-01-01 10:00:00", "2024-01-02 10:00:00", 1500, "brake issue"),
                "fetch": None,
                "result": None,
            },
            {
                "expect": "FROM schedule_assignments sa",
                "params": ("AAA-111",),
                "fetch": "all",
                "result": [],
            },
            {
                "expect": "DELETE FROM schedule_assignments",
                "params": ("AAA-111",),
                "fetch": None,
                "result": None,
            },
            {
                "expect": "UPDATE bus SET status = 'Service', line = '-'",
                "params": ("AAA-111",),
                "fetch": None,
                "result": None,
            },
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(hiba_service, 'get_connection', return_value=fake_conn):
            res = hiba_service.create_issue(data)
        self.assertEqual(res["message"], "Issue added and bus set to service")
        self.assertTrue(fake_conn.commit_called)
        q = fake_conn.cursor().queries
        self.assertIn("INSERT INTO issues", q[0])
        self.assertIn("FROM schedule_assignments sa", q[1])
        self.assertIn("DELETE FROM schedule_assignments", q[2])
        self.assertIn("UPDATE bus SET status = 'Service', line = '-'", q[3])

    def test_remove_issue(self):
        # Hiba nem található
        steps = [{
            "expect": "SELECT bus FROM issues WHERE id = %s",
            "params": (42,),
            "fetch": "one",
            "result": None,
        }]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(hiba_service, 'get_connection', return_value=fake_conn):
            res = hiba_service.remove_issue(42)
        self.assertIn("error", res)
        self.assertFalse(fake_conn.commit_called)
        self.assertIn("SELECT bus FROM issues", fake_conn.cursor().queries[0])

        # Busz utolsó hibájának eltávolítása
        steps = [
            {
                "expect": "SELECT bus FROM issues WHERE id = %s",
                "params": (7,),
                "fetch": "one",
                "result": {"bus": "AAA-111"},
            },
            {
                "expect": "DELETE FROM issues WHERE id = %s",
                "params": (7,),
                "fetch": None,
                "result": None,
            },
            {
                "expect": "SELECT COUNT(*) AS issue_count FROM issues WHERE bus = %s",
                "params": ("AAA-111",),
                "fetch": "one",
                "result": {"issue_count": 0},
            },
            {
                "expect": "UPDATE bus SET status = 'KT', line = '-'",
                "params": ("AAA-111",),
                "fetch": None,
                "result": None,
            },
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(hiba_service, 'get_connection', return_value=fake_conn):
            res = hiba_service.remove_issue(7)
        self.assertIn("status set to KT", res["message"])
        self.assertTrue(fake_conn.commit_called)

        # Busz nem utolsó hibájának eltávolítása
        steps = [
            {
                "expect": "SELECT bus FROM issues WHERE id = %s",
                "params": (8,),
                "fetch": "one",
                "result": {"bus": "BBB-222"},
            },
            {
                "expect": "DELETE FROM issues WHERE id = %s",
                "params": (8,),
                "fetch": None,
                "result": None,
            },
            {
                "expect": "SELECT COUNT(*) AS issue_count FROM issues WHERE bus = %s",
                "params": ("BBB-222",),
                "fetch": "one",
                "result": {"issue_count": 2},
            },
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(hiba_service, 'get_connection', return_value=fake_conn):
            res = hiba_service.remove_issue(8)
        self.assertIn("remains in Service", res["message"])
        self.assertTrue(fake_conn.commit_called)

if __name__ == "__main__":
    unittest.main()
