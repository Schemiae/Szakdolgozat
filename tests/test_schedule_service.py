import unittest
from unittest.mock import patch
from datetime import datetime
from flask_app.services import schedule_service
from db_fakes import FakeConnection

class TestScheduleService(unittest.TestCase):
    def test_generate_slots(self):
        slots = schedule_service.generate_slots("08:00", "10:00", 30)
        self.assertEqual(slots, ["08:00", "08:30", "09:00", "09:30", "10:00"])

    def test_plan_buses_for_schedule(self):
        schedule_row = {
            "id": 5,
            "username": "alice",
            "line_name": "10",
            "garage_id": 1,
            "frame": "midday",
            "start_time": datetime(2024, 1, 1, 8, 0),
            "end_time": datetime(2024, 1, 1, 10, 0),
            "frequency": 60,
            "bid_price": 5000,
            "status": "pending"
        }
        steps = [
            {
                "expect": "FROM schedules WHERE id = %s",
                "params": (5,),
                "fetch": "one",
                "result": schedule_row,
            },
            {
                "expect": "FROM lines WHERE name = %s",
                "params": ("10",),
                "fetch": "one",
                "result": {"travel_time_garage": 10, "travel_time_line": 30},
            },
            {
                "expect": "FROM schedule_assignments WHERE schedule_id = %s",
                "params": (5,),
                "fetch": "all",
                "result": [],
            },
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(schedule_service, 'get_connection', return_value=fake_conn):
            plan = schedule_service.plan_buses_for_schedule(5)
        self.assertEqual(plan["schedule_id"], 5)
        self.assertEqual(plan["line_name"], "10")
        self.assertEqual(plan["frequency"], 60)
        self.assertEqual(plan["slots"], ["08:00", "09:00", "10:00"])
        self.assertEqual(plan["buses_used"], 1)
        self.assertEqual(len(plan["assignments"]), 1)
        self.assertIn("duty_start", plan["assignments"][0])

    def test_has_all_assignments(self):
        schedule_row = {
            "id": 6,
            "username": "alice",
            "line_name": "10",
            "garage_id": 1,
            "frame": "midday",
            "start_time": datetime(2024, 1, 1, 8, 0),
            "end_time": datetime(2024, 1, 1, 10, 0),
            "frequency": 120,
            "bid_price": 4000,
            "status": "pending"
        }
        steps = [
            {
                "expect": "FROM schedules WHERE id = %s",
                "params": (6,),
                "fetch": "one",
                "result": schedule_row,
            },
            {
                "expect": "FROM lines WHERE name = %s",
                "params": ("10",),
                "fetch": "one",
                "result": {"travel_time_garage": 10, "travel_time_line": 30},
            },
            {
                "expect": "FROM schedule_assignments WHERE schedule_id = %s",
                "params": (6,),
                "fetch": "all",
                "result": [{"block_idx": 0, "bus_plate": "AAA-111"}],
            },
            {
                "expect": "SELECT COUNT(*) AS count FROM schedule_assignments",
                "params": (6,),
                "fetch": "one",
                "result": {"count": 1},
            },
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(schedule_service, 'get_connection', return_value=fake_conn):
            ok = schedule_service.has_all_assignments(6)
        self.assertTrue(ok)

    def test_select_winner_for_line_frame(self):
        schedules_fetch = [
            {"id": 1, "frequency": 30, "bid_price": 5000},
            {"id": 2, "frequency": 60, "bid_price": 4000},
        ]
        schedule_row_1 = {
            "id": 1,
            "username": "alice",
            "line_name": "10",
            "garage_id": 1,
            "frame": "midday",
            "start_time": datetime(2024, 1, 1, 8, 0),
            "end_time": datetime(2024, 1, 1, 10, 0),
            "frequency": 30,
            "bid_price": 5000,
            "status": "pending"
        }
        schedule_row_2 = {
            "id": 2,
            "username": "bob",
            "line_name": "10",
            "garage_id": 1,
            "frame": "midday",
            "start_time": datetime(2024, 1, 1, 8, 0),
            "end_time": datetime(2024, 1, 1, 10, 0),
            "frequency": 60,
            "bid_price": 4000,
            "status": "pending"
        }
        steps = [
            {
                "expect": "FROM schedules",
                "params": ("10", "midday"),
                "fetch": "all",
                "result": schedules_fetch,
            },
            {
                "expect": "FROM schedules WHERE id = %s",
                "params": (1,),
                "fetch": "one",
                "result": schedule_row_1,
            },
            {
                "expect": "FROM lines WHERE name = %s",
                "params": ("10",),
                "fetch": "one",
                "result": {"travel_time_garage": 10, "travel_time_line": 30},
            },
            {
                "expect": "FROM schedule_assignments WHERE schedule_id = %s",
                "params": (1,),
                "fetch": "all",
                "result": [
                    {"block_idx": 0, "bus_plate": "AAA-111"},
                    {"block_idx": 1, "bus_plate": "AAA-222"},
                ],
            },
            {
                "expect": "SELECT COUNT(*) AS count FROM schedule_assignments",
                "params": (1,),
                "fetch": "one",
                "result": {"count": 2},
            },
            {
                "expect": "FROM schedules WHERE id = %s",
                "params": (2,),
                "fetch": "one",
                "result": schedule_row_2,
            },
            {
                "expect": "FROM lines WHERE name = %s",
                "params": ("10",),
                "fetch": "one",
                "result": {"travel_time_garage": 10, "travel_time_line": 30},
            },
            {
                "expect": "FROM schedule_assignments WHERE schedule_id = %s",
                "params": (2,),
                "fetch": "all",
                "result": [
                    {"block_idx": 0, "bus_plate": "BBB-333"},
                ],
            },
            {
                "expect": "SELECT COUNT(*) AS count FROM schedule_assignments",
                "params": (2,),
                "fetch": "one",
                "result": {"count": 1},
            },
            {
                "expect": "UPDATE schedules SET status =",
                "params": ("active", 1),
                "fetch": None,
                "result": None,
            },
            {
                "expect": "UPDATE schedules SET status =",
                "params": ("lost", 2),
                "fetch": None,
                "result": None,
            },
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(schedule_service, 'get_connection', return_value=fake_conn):
            winner = schedule_service.select_winner_for_line_frame("10", "midday")
        self.assertEqual(winner, 1)
        self.assertTrue(fake_conn.commit_called)
        self.assertTrue(any("UPDATE schedules SET status" in q for q in fake_conn.cursor().queries))

if __name__ == "__main__":
    unittest.main()
