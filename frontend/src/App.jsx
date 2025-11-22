import { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, useLocation } from "react-router-dom";
import axios from "axios";
import Auth from "./Auth";
import Navbar from "./components/Navbar";
import Market from "./Market";
import Issues from "./Issues";
import Garages from "./Garages";
import Lines from "./Lines";
import Schedules from "./Schedules";
import "./App.css";

function EditDescription({ bus, onUpdated }) {
  const [editing, setEditing] = useState(false);
  const [desc, setDesc] = useState(bus.description || "");
  const [originalDesc, setOriginalDesc] = useState(bus.description || ""); 
  const [saving, setSaving] = useState(false);
  const [alertDlg, setAlertDlg] = useState({ open: false, title: "", message: "" });

  const handleSave = () => {
    setSaving(true);
    axios
      .put(
        `http://localhost:5000/busz/${bus.plate}`,
        { ...bus, description: desc },
        { withCredentials: true }
      )
      .then(() => {
        setOriginalDesc(desc);
        setEditing(false);
        setSaving(false);
        onUpdated(desc);
      })
      .catch(() => {
        setAlertDlg({ open: true, title: "Error", message: "Failed to update description" });
        setSaving(false);
      });
  };

  if (!editing) {
    return (
      <>
        <span className="ml-2">{bus.description || ""}</span>
        <button
          className="btn-industrial btn-industrial--secondary ml-2 px-2 py-1 bg-blue-500 text-black rounded hover:bg-blue-600"
          onClick={() => {
            setOriginalDesc(bus.description || "");
            setDesc(bus.description || "");
            setEditing(true);
          }}
        >
          Edit
        </button>
        {alertDlg.open && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
            <div className="panel bg-white border-4 border-red-600 rounded-2xl p-6 w-full max-w-md shadow-lg">
              <h3 className="text-xl font-bold text-red-800 mb-2">{alertDlg.title}</h3>
              <p className="text-gray-800 mb-4">{alertDlg.message}</p>
              <div className="flex justify-end">
                <button className="btn-industrial btn-industrial--secondary px-4 py-2 rounded" onClick={() => setAlertDlg({ open: false, title: "", message: "" })}>
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  return (
    <div className="flex flex-col gap-2 mt-2">
      <textarea
        className="border rounded p-2"
        value={desc}
        onChange={e => setDesc(e.target.value)}
        rows={2}
      />
      <div className="flex gap-2">
        <button
          className="px-3 py-1 bg-green-500 text-black rounded hover:bg-green-600"
          onClick={handleSave}
          disabled={saving}
        >
          Save
        </button>
        <button
          className="px-3 py-1 bg-gray-300 rounded hover:bg-gray-400"
          onClick={() => {
            setDesc(originalDesc);
            setEditing(false);
          }}
          disabled={saving}
        >
          Cancel
        </button>
      </div>
      {alertDlg.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="panel bg-white border-4 border-red-600 rounded-2xl p-6 w-full max-w-md shadow-lg">
            <h3 className="text-xl font-bold text-red-800 mb-2">{alertDlg.title}</h3>
            <p className="text-gray-800 mb-4">{alertDlg.message}</p>
            <div className="flex justify-end">
              <button className="btn-industrial btn-industrial--secondary px-4 py-2 rounded" onClick={() => setAlertDlg({ open: false, title: "", message: "" })}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function AppRoutes({
  loggedIn,
  setLoggedIn,
  loading,
  handleLogout,
  balance,
  fetchBalance,
  buses,
  setBuses,
  calculatePrice,
}) {
  const location = useLocation();
  const [showFavourites, setShowFavourites] = useState(false);
  const [garages, setGarages] = useState([]);
  const [openGarageFor, setOpenGarageFor] = useState(null);
  const [issuesByBus, setIssuesByBus] = useState({});
  const [alertDlg, setAlertDlg] = useState({ open: false, title: "", message: "" });

  const displayStatus = (s) => {
    if (!s) return s;
    const v = String(s).toLowerCase();
    if (v === "kt") return "Standby";
    if (v === "menetrend") return "Active";
    if (v === "service") return "Broken";
    return s;
  };

  useEffect(() => {
    if (location.pathname === "/" && loggedIn) {
      fetchBuses();
      axios
        .get("http://localhost:5000/garages", { withCredentials: true })
        .then((res) => setGarages(res.data || []))
        .catch(() => setGarages([]));
      axios
        .get("http://localhost:5000/hibak", { withCredentials: true })
        .then((res) => {
          const list = Array.isArray(res.data) ? res.data : [];
          const grouped = list.reduce((acc, it) => {
            const plate = it.bus || it.rendszam || it.plate;
            if (!plate) return acc;
            (acc[plate] = acc[plate] || []).push(it);
            return acc;
          }, {});
          setIssuesByBus(grouped);
        })
        .catch(() => setIssuesByBus({}));
    }
  }, [location, loggedIn]);

  function fetchBuses() {
    axios
      .get("http://localhost:5000/buszok", { withCredentials: true })
      .then((res) => setBuses(res.data))
      .catch((err) => console.error(err));
  }

  function handleToggleFavourite(plate) {
    axios
      .post(`http://localhost:5000/busz/${plate}/favourite`, {}, { withCredentials: true })
      .then(() => fetchBuses())
      .catch(() => setAlertDlg({ open: true, title: "Error", message: "Failed to toggle favourite" }));
  }

  const garageNameById = (id) => {
    const g = (garages || []).find((x) => String(x.id) === String(id));
    return g?.name || (id ?? "-");
  };
  const unlockedGarages = (garages || []).filter((g) => g.unlocked);

  const handleChangeGarage = (bus, newGarageId) => {
    if (!newGarageId) return;
    if (bus.status !== "KT") {
      alert("You can only move buses that are in Standby status.");
      return;
    }
    axios
      .put(
        `http://localhost:5000/busz/${bus.plate}`,
        { ...bus, garage: parseInt(newGarageId, 10) },
        { withCredentials: true }
      )
      .then(() => fetchBuses())
      .catch((err) => setAlertDlg({ open: true, title: "Error", message: err.response?.data?.error || "Failed to change garage" }));
  };

  if (loading) return <div className="text-center mt-20">Loading...</div>;
  if (!loggedIn) return <Auth onLogin={() => setLoggedIn(true)} />;

  return (
    <>
      {alertDlg.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="panel bg-white border-4 border-red-600 rounded-2xl p-6 w-full max-w-md shadow-lg">
            <h3 className="text-xl font-bold text-red-800 mb-2">{alertDlg.title || "Error"}</h3>
            <p className="text-gray-800 mb-4">{alertDlg.message}</p>
            <div className="flex justify-end">
              <button className="btn-industrial btn-industrial--secondary px-4 py-2 rounded" onClick={() => setAlertDlg({ open: false, title: "", message: "" })}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      <Navbar onLogout={handleLogout} balance={balance} />
      <div className="min-h-screen min-w-screen flex flex-col justify-top items-center p-6">
        <div className="w-full max-w-6xl mx-auto">
          <Routes>
            <Route
              path="/"
              element={
                <>
                  <div className="flex items-center justify-between mb-6">
                    <h1 className="section-title text-3xl font-bold">Your Buses</h1>
                    <button
                      className={`btn-industrial btn-industrial--secondary px-4 py-2 rounded text-lg transition ${showFavourites ? "bg-yellow-300 text-yellow-900" : "bg-gray-300 text-gray-900 hover:bg-gray-400"}`}
                      onClick={() => setShowFavourites((fav) => !fav)}
                    >
                      {showFavourites ? "⭐ Showing Favourites" : "⚝ Show All"}
                    </button>
                  </div>

                  <div className="w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {(showFavourites ? buses.filter((bus) => bus.favourite) : buses).map((bus) => {
                      const issues = issuesByBus[bus.plate] || [];
                      const statusLabel = displayStatus(bus.status);
                      const statusClass = statusLabel === "Active"
                        ? "bg-green-100 text-green-800 border border-green-300"
                        : statusLabel === "Broken"
                          ? "bg-red-100 text-red-800 border border-red-300"
                          : "bg-gray-100 text-gray-800 border border-gray-300";
                      const sideClass = statusLabel === "Active" ? "bus-card--ok" : statusLabel === "Broken" ? "bus-card--broken" : "bus-card--idle";
                      return (
                        <div
                          key={bus.plate}
                          className={`bus-card ${sideClass} bg-white p-6 rounded-lg shadow-lg border-4 border-blue-800 hover:shadow-xl transition flex flex-col`}
                        >
                          <div className="flex items-center justify-between mb-4">
                            <h2 className="text-2xl font-bold text-blue-900">
                              <span className="mr-2" aria-hidden>🚌</span>
                              <span className="bus-plate">{bus.plate}</span>
                            </h2>
                            <button
                              onClick={() => handleToggleFavourite(bus.plate)}
                              className="text-2xl hover:scale-125 transition"
                              title={bus.favourite ? "Unfavourite" : "Favourite"}
                            >
                              {bus.favourite ? "⭐" : "⚝"}
                            </button>
                          </div>

                          <div className="space-y-3 mb-4 flex-grow">
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <p className="bus-meta-label text-xs text-gray-600 font-semibold">TYPE</p>
                                <p className="text-lg emph text-gray-800">{bus.type}</p>
                              </div>
                              <div>
                                <p className="bus-meta-label text-xs text-gray-600 font-semibold">KM</p>
                                <p className="text-lg emph text-gray-800">{bus.km?.toLocaleString?.() || bus.km}</p>
                              </div>
                              <div>
                                <p className="bus-meta-label text-xs text-gray-600 font-semibold">YEAR</p>
                                <p className="text-lg emph text-gray-800">{bus.year}</p>
                              </div>
                              <div>
                                <p className="bus-meta-label text-xs text-gray-600 font-semibold">GARAGE</p>
                                {bus.status === "KT" ? (
                                  <div className="relative inline-block text-left">
                                    <button
                                      type="button"
                                      className="inline-flex items-center border px-3 py-1 rounded hover:bg-gray-50"
                                      onClick={() => setOpenGarageFor(openGarageFor === bus.plate ? null : bus.plate)}
                                      title="Click to change garage"
                                    >
                                      <span className="emph">{garageNameById(bus.garage)}</span>
                                      <svg className="ml-2 h-4 w-4 text-gray-600" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                        <path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 111.06 1.06l-4.24 4.24a.75.75 0 01-1.06 0L5.21 8.29a.75.75 0 01.02-1.08z" clipRule="evenodd" />
                                      </svg>
                                    </button>
                                    {openGarageFor === bus.plate && (
                                      <div className="absolute z-10 mt-2 w-52 bg-white border rounded shadow-lg">
                                        {unlockedGarages.map((g) => (
                                          <button
                                            key={g.id}
                                            className={`block w-full text-left px-3 py-2 hover:bg-blue-50 ${String(bus.garage) === String(g.id) ? "font-semibold text-blue-700" : ""}`}
                                            onClick={() => {
                                              setOpenGarageFor(null);
                                              if (String(bus.garage) !== String(g.id)) {
                                                handleChangeGarage(bus, g.id);
                                              }
                                            }}
                                          >
                                            {g.name || `Garage #${g.id}`}
                                          </button>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                ) : (
                                  <p className="text-lg emph text-gray-800" title="Garage can be changed only when bus is in Standby">
                                    {garageNameById(bus.garage)}
                                  </p>
                                )}
                              </div>
                              <div>
                                <p className="bus-meta-label text-xs text-gray-600 font-semibold">STATUS</p>
                                <div className="text-lg emph">
                                  <span className={`px-2 py-0.5 rounded ${statusClass}`}>{statusLabel}</span>
                                </div>
                              </div>
                              <div>
                                <p className="bus-meta-label text-xs text-gray-600 font-semibold">LINE</p>
                                <div className="text-lg emph text-gray-800">
                                  {bus.line && bus.line !== '-' ? (
                                    <span className="line-plate">{bus.line}</span>
                                  ) : (
                                    <span className="text-gray-500">-</span>
                                  )}
                                </div>
                              </div>
                            </div>

                            <div className="bus-sep border-t pt-3">
                              <p className="bus-meta-label text-xs text-gray-600 font-semibold mb-1">DESCRIPTION</p>
                              <EditDescription bus={bus} onUpdated={() => fetchBuses()} />
                            </div>

                            {!!issues.length && (
                              <div className="bus-sep border-t pt-3">
                                <div className="flex items-center justify-between mb-1">
                                  <p className="bus-meta-label text-xs text-gray-600 font-semibold">Issues</p>
                                  <span className="text-xs font-semibold text-red-700">{issues.length}</span>
                                </div>
                                <ul className="text-sm text-gray-800 list-disc ml-5">
                                  {issues.slice(0, 3).map((it, idx) => (
                                    <li key={it.id || idx}>
                                      {it.description }
                                      {it.repair_time ? (
                                        <span className="text-xs text-gray-600"> — repair: {it.repair_time}</span>
                                      ) : null}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {buses.length === 0 && (
                    <div className="text-center mt-12 text-gray-500 text-lg">
                      No buses yet. Go to the Market to buy one!
                    </div>
                  )}
                </>
              }
            />
            <Route path="/market" element={<Market onPurchase={fetchBalance} />} />
            <Route path="/schedules" element={<Schedules />} />
            <Route path="/lines" element={<Lines />} />
            <Route path="/garages" element={<Garages balance={balance} fetchBalance={fetchBalance} />} />
            <Route path="/issues" element={<Issues balance={balance} fetchBalance={fetchBalance} />} />
          </Routes>
        </div>
      </div>
    </>
  );
}

export default function App() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);
  const [buses, setBuses] = useState([]);
  const [balance, setBalance] = useState(null);

  useEffect(() => {
    axios
      .get("http://localhost:5000/session", { withCredentials: true })
      .then((res) => {
        if (res.data.logged_in) setLoggedIn(true);
      })
      .catch(() => setLoggedIn(false))
      .finally(() => setLoading(false));
  }, []);
  useEffect(() => {
    if (loggedIn) {
      fetchBalance();
    }
  }, [loggedIn]);

  const fetchBalance = () => {
    axios.get("http://localhost:5000/user/balance", { withCredentials: true })
      .then(res => setBalance(res.data.balance))
      .catch(() => setBalance(null));
  };

  const calculatePrice = (km) => {
    const basePrice = 100000;
    const minPrice = 10000;
    const maxKm = 500_000;
    const price = basePrice - (km / maxKm) * (basePrice - minPrice);
    return Math.round(Math.max(price, minPrice));
  };

  const handleLogout = () => {
    axios
      .post("http://localhost:5000/logout", {}, { withCredentials: true })
      .then(() => setLoggedIn(false));
  };

  return (
    <Router>
      <AppRoutes
        loggedIn={loggedIn}
        setLoggedIn={setLoggedIn}
        loading={loading}
        handleLogout={handleLogout}
        balance={balance}
        fetchBalance={fetchBalance}
        buses={buses}
        setBuses={setBuses}
        calculatePrice={calculatePrice}
      />
    </Router>
  );
}