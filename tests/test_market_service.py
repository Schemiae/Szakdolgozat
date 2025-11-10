import unittest
from unittest.mock import patch
from flask_app.services import market_service
from db_fakes import FakeConnection

class TestMarketService(unittest.TestCase):
    def test_list_market_buses(self):
        rows = [
            {"plate": "AAA-111", "type": "Volvo", "km": 1000, "year": 2005, "garage": None, "owner": None},
            {"plate": "BBB-222", "type": "Ikarus", "km": 2000, "year": 1999, "garage": None, "owner": None},
        ]
        steps = [{
            "expect": "FROM bus WHERE owner IS NULL",
            "params": None,
            "fetch": "all",
            "result": rows,
        }]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(market_service, 'get_connection', return_value=fake_conn):
            res = market_service.list_market_buses()
        self.assertEqual(res, rows)
        self.assertIn("FROM bus WHERE owner IS NULL", fake_conn.cursor().queries[0])
        self.assertIsNone(fake_conn.cursor().params_list[0])
        self.assertFalse(fake_conn.commit_called)

    def test_list_new_bus_models(self):
        res = market_service.list_new_bus_models()
        self.assertTrue(isinstance(res, list) and len(res) > 0)
        self.assertTrue(all(set(["key", "label", "tipus", "evjarat", "price"]).issubset(r.keys()) for r in res))

    def test_list_active_listings(self):
        rows = [
            {"listing_id": 1, "bus_plate": "AAA-111", "seller_username": "bob", "price": 120000, "created_at": "t",
             "type": "Volvo", "km": 1000, "year": 2005, "garage": 1},
        ]
        steps = [{
            "expect": "FROM market_listings ml",
            "params": None,
            "fetch": "all",
            "result": rows,
        }]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(market_service, 'get_connection', return_value=fake_conn):
            res = market_service.list_active_listings()
        self.assertEqual(res, rows)
        self.assertIn("WHERE ml.status = 'active'", fake_conn.cursor().queries[0])

    def test_create_listing(self):
        # Sikeres hirdetés létrehozás
        steps = [
            {"expect": "SELECT owner FROM bus", "params": ("AAA-111",), "fetch": "one", "result": {"owner": "alice"}},
            {"expect": "SELECT 1 FROM market_listings", "params": ("AAA-111",), "fetch": "one", "result": None},
            {"expect": "INSERT INTO market_listings", "params": ("AAA-111", "alice", 130000), "fetch": "one", "result": {"id": 10}},
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(market_service, 'get_connection', return_value=fake_conn):
            res, status = market_service.create_listing("alice", "AAA-111", 130000)
        self.assertEqual(status, 200)
        self.assertEqual(res["listing_id"], 10)
        self.assertTrue(fake_conn.commit_called)

        # Sikertelen hirdetés létrehozás - nem a felhasználó a tulajdonos
        steps = [{"expect": "SELECT owner FROM bus", "params": ("AAA-111",), "fetch": "one", "result": {"owner": "bob"}}]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(market_service, 'get_connection', return_value=fake_conn):
            res, status = market_service.create_listing("alice", "AAA-111", 130000)
        self.assertEqual(status, 400)
        self.assertIn("You do not own this bus", res["error"])
        self.assertFalse(fake_conn.commit_called)

        # Sikertelen hirdetés létrehozás - már létezik hirdetés az adott buszra
        steps = [
            {"expect": "SELECT owner FROM bus", "params": ("AAA-111",), "fetch": "one", "result": {"owner": "alice"}},
            {"expect": "SELECT 1 FROM market_listings", "params": ("AAA-111",), "fetch": "one", "result": {"x": 1}},
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(market_service, 'get_connection', return_value=fake_conn):
            res, status = market_service.create_listing("alice", "AAA-111", 130000)
        self.assertEqual(status, 400)
        self.assertIn("already listed", res["error"])
        self.assertFalse(fake_conn.commit_called)

    def test_cancel_listing(self):
        # Sikertelen hirdetés törlés - hirdetés nem található
        steps = [{"expect": "SELECT id, seller_username, status FROM market_listings", "params": (5,), "fetch": "one", "result": None}]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(market_service, 'get_connection', return_value=fake_conn):
            res, status = market_service.cancel_listing("alice", 5)
        self.assertEqual(status, 404)
        self.assertIn("not found", res["error"])
        self.assertFalse(fake_conn.commit_called)

        # Sikertelen hirdetés törlés - nem a felhasználó a hirdető
        steps = [{"expect": "SELECT id, seller_username, status FROM market_listings", "params": (5,), "fetch": "one", "result": {"id": 5, "seller_username": "bob", "status": "active"}}]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(market_service, 'get_connection', return_value=fake_conn):
            res, status = market_service.cancel_listing("alice", 5)
        self.assertEqual(status, 403)
        self.assertIn("Not your listing", res["error"])
        self.assertFalse(fake_conn.commit_called)

        # Sikeres hirdetés törlés
        steps = [
            {"expect": "SELECT id, seller_username, status FROM market_listings", "params": (5,), "fetch": "one", "result": {"id": 5, "seller_username": "alice", "status": "active"}},
            {"expect": "UPDATE market_listings SET status = 'canceled'", "params": (5,), "fetch": None, "result": None},
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(market_service, 'get_connection', return_value=fake_conn):
            res, status = market_service.cancel_listing("alice", 5)
        self.assertEqual(status, 200)
        self.assertIn("canceled", res["message"])
        self.assertTrue(fake_conn.commit_called)

    def test_purchase_listing(self):
        # Sikeres hirdetés vásárlás
        steps = [
            {"expect": "FROM market_listings WHERE id = %s FOR UPDATE", "params": (7,), "fetch": "one", "result": {"id": 7, "bus_plate": "AAA-111", "seller_username": "bob", "price": 120000, "status": "active"}},
            {"expect": "SELECT owner FROM bus", "params": ("AAA-111",), "fetch": "one", "result": {"owner": "bob"}},
            {"expect": "SELECT balance FROM users", "params": ("alice",), "fetch": "one", "result": {"balance": 200000}},
            {"expect": "SELECT 1 FROM user_garages", "params": ("alice", 3), "fetch": "one", "result": {"x": 1}},
            {"expect": "FROM schedule_assignments sa", "params": ("AAA-111",), "fetch": "all", "result": []},
            {"expect": "DELETE FROM schedule_assignments", "params": ("AAA-111",), "fetch": None, "result": None},
            {"expect": "UPDATE users SET balance = balance -", "params": (120000, "alice"), "fetch": None, "result": None},
            {"expect": "UPDATE users SET balance = balance +", "params": (120000, "bob"), "fetch": None, "result": None},
            {"expect": "UPDATE bus", "params": ("alice", 3, "AAA-111"), "fetch": None, "result": None},
            {"expect": "UPDATE market_listings SET status = 'sold'", "fetch": None, "result": None},
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(market_service, 'get_connection', return_value=fake_conn):
            res, status = market_service.purchase_listing("alice", 7, garage_id=3)
        self.assertEqual(status, 200)
        self.assertIn("Purchase successful", res["message"])
        self.assertTrue(fake_conn.commit_called)

        # Sikertelen hirdetés vásárlás - hirdetés nem elérhető
        steps = [{"expect": "FROM market_listings WHERE id = %s FOR UPDATE", "params": (7,), "fetch": "one", "result": {"id": 7, "bus_plate": "AAA-111", "seller_username": "bob", "price": 120000, "status": "sold"}}]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(market_service, 'get_connection', return_value=fake_conn):
            res, status = market_service.purchase_listing("alice", 7)
        self.assertEqual(status, 404)
        self.assertIn("not available", res["error"])
        self.assertFalse(fake_conn.commit_called)

        # Sikertelen hirdetés vásárlás - a felhasználó a saját hirdetését próbálja megvenni
        steps = [{"expect": "FROM market_listings WHERE id = %s FOR UPDATE", "params": (7,), "fetch": "one", "result": {"id": 7, "bus_plate": "AAA-111", "seller_username": "alice", "price": 120000, "status": "active"}}]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(market_service, 'get_connection', return_value=fake_conn):
            res, status = market_service.purchase_listing("alice", 7)
        self.assertEqual(status, 400)
        self.assertIn("own listing", res["error"])
        self.assertFalse(fake_conn.commit_called)

        # Sikertelen hirdetés vásárlás - az eladó már nem a tulajdonos
        steps = [
            {"expect": "FROM market_listings WHERE id = %s FOR UPDATE", "params": (7,), "fetch": "one", "result": {"id": 7, "bus_plate": "AAA-111", "seller_username": "bob", "price": 120000, "status": "active"}},
            {"expect": "SELECT owner FROM bus", "params": ("AAA-111",), "fetch": "one", "result": {"owner": "charlie"}},
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(market_service, 'get_connection', return_value=fake_conn):
            res, status = market_service.purchase_listing("alice", 7)
        self.assertEqual(status, 400)
        self.assertIn("Seller no longer owns", res["error"])
        self.assertFalse(fake_conn.commit_called)

        # Sikertelen hirdetés vásárlás - elégtelen egyenleg
        steps = [
            {"expect": "FROM market_listings WHERE id = %s FOR UPDATE", "params": (7,), "fetch": "one", "result": {"id": 7, "bus_plate": "AAA-111", "seller_username": "bob", "price": 120000, "status": "active"}},
            {"expect": "SELECT owner FROM bus", "params": ("AAA-111",), "fetch": "one", "result": {"owner": "bob"}},
            {"expect": "SELECT balance FROM users", "params": ("alice",), "fetch": "one", "result": {"balance": 50000}},
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(market_service, 'get_connection', return_value=fake_conn):
            res, status = market_service.purchase_listing("alice", 7)
        self.assertEqual(status, 400)
        self.assertIn("Insufficient balance", res["error"])
        self.assertFalse(fake_conn.commit_called)

        # Sikertelen hirdetés vásárlás - nincs feloldott garázs
        steps = [
            {"expect": "FROM market_listings WHERE id = %s FOR UPDATE", "params": (7,), "fetch": "one", "result": {"id": 7, "bus_plate": "AAA-111", "seller_username": "bob", "price": 120000, "status": "active"}},
            {"expect": "SELECT owner FROM bus", "params": ("AAA-111",), "fetch": "one", "result": {"owner": "bob"}},
            {"expect": "SELECT balance FROM users", "params": ("alice",), "fetch": "one", "result": {"balance": 200000}},
            {"expect": "SELECT garage_id FROM user_garages", "params": ("alice",), "fetch": "one", "result": None},
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(market_service, 'get_connection', return_value=fake_conn):
            res, status = market_service.purchase_listing("alice", 7)
        self.assertEqual(status, 400)
        self.assertIn("No unlocked garage", res["error"])
        self.assertFalse(fake_conn.commit_called)

    def test_buy_bus(self):
        # Sikeres busz vásárlás
        steps = [
            {"expect": "FROM bus WHERE plate = %s AND owner IS NULL", "params": ("AAA-111",), "fetch": "one", "result": {"plate": "AAA-111", "km": 0}},
            {"expect": "SELECT balance FROM users", "params": ("alice",), "fetch": "one", "result": {"balance": 150000}},
            {"expect": "SELECT 1 FROM user_garages", "params": ("alice", 2), "fetch": "one", "result": {"x": 1}},
            {"expect": "UPDATE users SET balance = balance -", "params": (120000, "alice"), "fetch": None, "result": None},
            {"expect": "UPDATE bus", "params": ("alice", 2, "AAA-111"), "fetch": None, "result": None},
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(market_service, 'get_connection', return_value=fake_conn):
            res, status = market_service.buy_bus("AAA-111", "alice", 120000, garage_id=2)
        self.assertEqual(status, 200)
        self.assertIn("You bought bus AAA-111", res["message"])
        self.assertTrue(fake_conn.commit_called)

        # Busz sikertelen vásárlása (nem elérhető busz)
        steps = [{"expect": "FROM bus WHERE plate = %s AND owner IS NULL", "params": ("AAA-111",), "fetch": "one", "result": None}]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(market_service, 'get_connection', return_value=fake_conn):
            res, status = market_service.buy_bus("AAA-111", "alice", 120000)
        self.assertEqual(status, 400)
        self.assertIn("not available", res["error"])
        self.assertFalse(fake_conn.commit_called)

        # Busz sikertelen vásárlása - felhasználó nem létezik
        steps = [
            {"expect": "FROM bus WHERE plate = %s AND owner IS NULL", "params": ("AAA-111",), "fetch": "one", "result": {"plate": "AAA-111", "km": 0}},
            {"expect": "SELECT balance FROM users", "params": ("alice",), "fetch": "one", "result": None},
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(market_service, 'get_connection', return_value=fake_conn):
            res, status = market_service.buy_bus("AAA-111", "alice", 120000)
        self.assertEqual(status, 404)
        self.assertIn("User not found", res["error"])
        self.assertFalse(fake_conn.commit_called)

        # Busz sikertelen vásárlása - elégtelen egyenleg
        steps = [
            {"expect": "FROM bus WHERE plate = %s AND owner IS NULL", "params": ("AAA-111",), "fetch": "one", "result": {"plate": "AAA-111", "km": 0}},
            {"expect": "SELECT balance FROM users", "params": ("alice",), "fetch": "one", "result": {"balance": 10000}},
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(market_service, 'get_connection', return_value=fake_conn):
            res, status = market_service.buy_bus("AAA-111", "alice", 120000)
        self.assertEqual(status, 400)
        self.assertIn("Insufficient balance", res["error"])
        self.assertFalse(fake_conn.commit_called)

    def test_purchase_new_bus(self):
        # Új busz sikeres vásárlása
        data = {"model_key": "Volvo", "rendszam": "XYZ-123", "leiras": "brand new", "garazs": 5}
        price = market_service.NEW_BUS_MODELS["Volvo"]["price"]
        steps = [
            {"expect": "SELECT 1 FROM user_garages", "params": ("alice", 5), "fetch": "one", "result": {"x": 1}},
            {"expect": "SELECT 1 FROM bus WHERE plate = %s", "params": ("XYZ-123",), "fetch": "one", "result": None},
            {"expect": "SELECT balance FROM users", "params": ("alice",), "fetch": "one", "result": {"balance": price + 1000}},
            {"expect": "UPDATE users SET balance = balance -", "params": (price, "alice"), "fetch": None, "result": None},
            {
                "expect": "INSERT INTO bus",
                "params": ("XYZ-123", market_service.NEW_BUS_MODELS["Volvo"]["tipus"], 0, market_service.NEW_BUS_MODELS["Volvo"]["evjarat"], 5, "brand new", "alice"),
                "fetch": None,
                "result": None,
            },
            {"expect": "SELECT balance FROM users", "params": ("alice",), "fetch": "one", "result": {"balance": 0}},
        ]
        fake_conn = FakeConnection(steps=steps)
        with patch.object(market_service, 'get_connection', return_value=fake_conn):
            res, status = market_service.purchase_new_bus(data, "alice")
        self.assertEqual(status, 200)
        self.assertIn("You bought a new", res["message"])
        self.assertTrue(fake_conn.commit_called)

        # Új busz sikertelen vásárlása
        # Nem létező modell
        fake_conn1 = FakeConnection(steps=[])
        with patch.object(market_service, 'get_connection', return_value=fake_conn1):
            res, status = market_service.purchase_new_bus({"model_key": "INVALID", "rendszam": "ABC-123", "leiras": "x", "garazs": 1}, "alice")
        self.assertEqual(status, 400)
        # Érvénytelen rendszám
        fake_conn2 = FakeConnection(steps=[])
        with patch.object(market_service, 'get_connection', return_value=fake_conn2):
            res, status = market_service.purchase_new_bus({"model_key": "Volvo", "rendszam": "bad", "leiras": "x", "garazs": 1}, "alice")
        self.assertEqual(status, 400)
        # Garázs nincs feloldva
        steps3 = [{"expect": "SELECT 1 FROM user_garages", "params": ("alice", 1), "fetch": "one", "result": None}]
        fake_conn3 = FakeConnection(steps=steps3)
        with patch.object(market_service, 'get_connection', return_value=fake_conn3):
            res, status = market_service.purchase_new_bus({"model_key": "Volvo", "rendszam": "ABC-123", "leiras": "x", "garazs": 1}, "alice")
        self.assertEqual(status, 400)
        # Már létező rendszám
        steps4 = [
            {"expect": "SELECT 1 FROM user_garages", "params": ("alice", 1), "fetch": "one", "result": {"x": 1}},
            {"expect": "SELECT 1 FROM bus WHERE plate = %s", "params": ("ABC-123",), "fetch": "one", "result": {"x": 1}},
        ]
        fake_conn4 = FakeConnection(steps=steps4)
        with patch.object(market_service, 'get_connection', return_value=fake_conn4):
            res, status = market_service.purchase_new_bus({"model_key": "Volvo", "rendszam": "ABC-123", "leiras": "x", "garazs": 1}, "alice")
        self.assertEqual(status, 400)
        # Felhasználó nem létezik
        price = market_service.NEW_BUS_MODELS["Volvo"]["price"]
        steps5 = [
            {"expect": "SELECT 1 FROM user_garages", "params": ("alice", 1), "fetch": "one", "result": {"x": 1}},
            {"expect": "SELECT 1 FROM bus WHERE plate = %s", "params": ("ABC-123",), "fetch": "one", "result": None},
            {"expect": "SELECT balance FROM users", "params": ("alice",), "fetch": "one", "result": None},
        ]
        fake_conn5 = FakeConnection(steps=steps5)
        with patch.object(market_service, 'get_connection', return_value=fake_conn5):
            res, status = market_service.purchase_new_bus({"model_key": "Volvo", "rendszam": "ABC-123", "leiras": "x", "garazs": 1}, "alice")
        self.assertEqual(status, 404)
        # Elégtelen egyenleg
        steps6 = [
            {"expect": "SELECT 1 FROM user_garages", "params": ("alice", 1), "fetch": "one", "result": {"x": 1}},
            {"expect": "SELECT 1 FROM bus WHERE plate = %s", "params": ("ABC-123",), "fetch": "one", "result": None},
            {"expect": "SELECT balance FROM users", "params": ("alice",), "fetch": "one", "result": {"balance": price - 1}},
        ]
        fake_conn6 = FakeConnection(steps=steps6)
        with patch.object(market_service, 'get_connection', return_value=fake_conn6):
            res, status = market_service.purchase_new_bus({"model_key": "Volvo", "rendszam": "ABC-123", "leiras": "x", "garazs": 1}, "alice")
        self.assertEqual(status, 400)

if __name__ == "__main__":
    unittest.main()
