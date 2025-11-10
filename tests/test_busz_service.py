import unittest
from unittest.mock import patch
from flask_app.services import busz_service
from db_fakes import FakeConnection

class TestBuszService(unittest.TestCase):

    def test_get_buses_for_user(self):
        # Lekérdezés létező felhasználóra
        rows = [
            {"plate": "AAA-111", "type": "Ikarus", "km": 1000, "year": 2000, "garage": 1,
             "description": "Bus 1", "status": "KT", "line": "-", "owner": "alice", "favourite": False},
        ]
        steps = [{
            "expect": "WHERE owner = %s",
            "params": ("alice",),
            "fetch": "all",
            "result": rows,
        }]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(busz_service, 'get_connection', return_value=fake_conn):
            result = busz_service.get_buses_for_user("alice", False)
        self.assertEqual(len(result), 1)
        self.assertIn("WHERE owner = %s", fake_conn.cursor().queries[0])
        self.assertEqual(fake_conn.cursor().params_list[0], ("alice",))
        self.assertEqual(result[0]["owner"], "alice")

        # Lekérdezés nem létező felhasználóra
        steps = [{
            "expect": "FROM bus",
            "params": ("nobody",),
            "fetch": "all",
            "result": [],
        }]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(busz_service, 'get_connection', return_value=fake_conn):
            result = busz_service.get_buses_for_user("nobody", False)
        self.assertEqual(result, [])

    def test_create_bus(self):
        # Új busz sikeres létrehozása
        data = {
            "plate": "CCC-333", "type": "Mercedes", "km": 500,
            "year": 2010, "garage": 3, "description": "New bus",
            "status": "KT", "line": "-"
        }
        steps = [{
            "expect": "INSERT INTO bus",
            "params": ("CCC-333", "Mercedes", 500, 2010, 3, "New bus", "KT", "-"),
            "fetch": None,
            "result": None,
            "rowcount": 1,
        }]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(busz_service, 'get_connection', return_value=fake_conn):
            res = busz_service.create_bus(data)
        self.assertEqual(res["message"], "Bus added")
        self.assertTrue(fake_conn.commit_called)
        self.assertEqual(fake_conn.commit_count, 1)
        self.assertIn("INSERT INTO bus", fake_conn.cursor().queries[0])
        self.assertEqual(fake_conn.cursor().params_list[0], steps[0]["params"])

        # Új busz létrehozása hiányzó mezőkkel
        bad_data = {
            "plate": "CCC-333", "type": "Mercedes",
            "year": 2010, "garage": 3, "description": "New bus",
            "status": "KT", "line": "-"
        }
        fake_conn = FakeConnection(steps=[]) 
        with patch.object(busz_service, 'get_connection', return_value=fake_conn):
            with self.assertRaises(ValueError):
                busz_service.create_bus(bad_data)
        self.assertFalse(fake_conn.commit_called)

    def test_update_bus(self):
        # Busz sikeres frissítése
        data = {
            "type": "Renault", "km": 1500, "year": 2012,
            "garage": 2, "description": "Updated", "status": "KT", "line": "-"
        }
        steps = [{
            "expect": "UPDATE bus",
            "params": ("Renault", 1500, 2012, 2, "Updated", "KT", "-", "AAA-111"),
            "fetch": None,
            "result": None,
            "rowcount": 1,
        }]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(busz_service, 'get_connection', return_value=fake_conn):
            res = busz_service.update_bus("AAA-111", data)
        self.assertIn("updated", res["message"])
        self.assertTrue(fake_conn.commit_called)
        self.assertEqual(fake_conn.commit_count, 1)
        self.assertIn("UPDATE bus", fake_conn.cursor().queries[0])
        self.assertEqual(fake_conn.cursor().params_list[0], steps[0]["params"])

        # Busz sikertelen frissítése (nem létező rendszám)
        data = {
            "type": "Renault", "km": 1500, "year": 2012,
            "garage": 2, "description": "Updated", "status": "KT", "line": "-"
        }
        steps = [{
            "expect": "UPDATE bus",
            "params": ("Renault", 1500, 2012, 2, "Updated", "KT", "-", "ZZZ-999"),
            "fetch": None,
            "result": None,
            "rowcount": 0,
        }]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(busz_service, 'get_connection', return_value=fake_conn):
            res, status = busz_service.update_bus("ZZZ-999", data)
        self.assertEqual(status, 404)
        self.assertIn("not found", res["error"])
        self.assertFalse(fake_conn.commit_called)

    def test_toggle_favourite(self):
        # Kedvenc státusz sikeres váltása
        steps = [{
            "expect": "UPDATE bus SET favourite = NOT favourite",
            "params": ("AAA-111", "alice"),
            "fetch": None,
            "result": None,
            "rowcount": 1,
        }]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(busz_service, 'get_connection', return_value=fake_conn):
            res = busz_service.toggle_favourite("AAA-111", "alice")
        self.assertEqual(res["message"], "Favourite toggled")
        self.assertTrue(fake_conn.commit_called)
        self.assertIn("UPDATE bus SET favourite = NOT favourite", fake_conn.cursor().queries[0])
        self.assertEqual(fake_conn.cursor().params_list[0], ("AAA-111", "alice"))

        # Kedvenc státusz váltása sikertelen (nem a felhasználó busza)
        steps = [{
            "expect": "UPDATE bus SET favourite = NOT favourite",
            "params": ("AAA-111", "alice"),
            "fetch": None,
            "result": None,
            "rowcount": 0,
        }]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(busz_service, 'get_connection', return_value=fake_conn):
            res, status = busz_service.toggle_favourite("AAA-111", "alice")
        self.assertEqual(status, 404)
        self.assertIn("not found", res["error"])
        self.assertFalse(fake_conn.commit_called)

if __name__ == "__main__":
    unittest.main()
