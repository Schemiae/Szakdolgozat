import { useEffect, useState } from "react";
import axios from "axios";

export default function Garages({ balance, fetchBalance }) {
  const [garages, setGarages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [buses, setBuses] = useState([]);

  const [confirm, setConfirm] = useState({ open: false, title: "", message: "", onConfirm: null });
  const openConfirm = (title, message, onConfirm) => setConfirm({ open: true, title, message, onConfirm });
  const closeConfirm = () => setConfirm({ open: false, title: "", message: "", onConfirm: null });

  const [alertDlg, setAlertDlg] = useState({ open: false, title: "", message: "" });
  const openAlert = (title, message) => setAlertDlg({ open: true, title, message });
  const closeAlert = () => setAlertDlg({ open: false, title: "", message: "" });

  const fetchGarages = () => {
    axios.get("http://localhost:5000/garages", { withCredentials: true })
      .then(res => setGarages(res.data))
      .catch(() => setGarages([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchGarages();
    axios.get("http://localhost:5000/buszok", { withCredentials: true })
      .then(res => setBuses(res.data || []))
      .catch(() => setBuses([]));
  }, []);

  const unlockedCount = (garages || []).filter(g => g.unlocked).length;

  const handleUnlock = (garageId, price) => {
    const isFree = unlockedCount === 0;
    if (!isFree && balance < price) {
      openAlert("Insufficient balance", `You need ${price.toLocaleString()} 💰 to unlock this garage.`);
      return;
    }
    axios.post("http://localhost:5000/garage/unlock", { garage_id: garageId }, { withCredentials: true })
      .then(res => {
        fetchBalance();
        fetchGarages();
        return axios.get("http://localhost:5000/buszok", { withCredentials: true });
      })
      .then(resp => setBuses(resp?.data || buses))
      .catch(err => openAlert("Error", err.response?.data?.error || "Failed to unlock garage"));
  };

  if (loading) return <div className="text-center mt-20">Loading garages...</div>;

  const busesByGarage = (buses || []).reduce((acc, b) => {
    const gid = String(b.garage);
    (acc[gid] = acc[gid] || []).push(b);
    return acc;
  }, {});

  const displayStatus = (s) => {
    if (!s) return s;
    const v = String(s).toLowerCase();
    if (v === "kt") return "Standby";
    if (v === "menetrend") return "Active";
    if (v === "service") return "Broken";
    return s;
  };

  return (
    <div className="max-w-5xl mx-auto mt-8">
      {confirm.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="panel bg-white border-4 border-blue-800 rounded-2xl p-6 w-full max-w-md shadow-lg">
            <h3 className="text-xl font-bold text-blue-900 mb-2">{confirm.title}</h3>
            <p className="text-gray-800 mb-4">{confirm.message}</p>
            <div className="flex justify-end gap-2">
              <button className="btn-industrial btn-industrial--secondary px-4 py-2 rounded" onClick={closeConfirm}>
                Cancel
              </button>
              <button
                className="btn-industrial btn-industrial--primary px-4 py-2 rounded"
                onClick={() => {
                  confirm.onConfirm && confirm.onConfirm();
                  closeConfirm();
                }}
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}

      {alertDlg.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="panel bg-white border-4 border-red-600 rounded-2xl p-6 w-full max-w-md shadow-lg">
            <h3 className="text-xl font-bold text-red-800 mb-2">{alertDlg.title || "Error"}</h3>
            <p className="text-gray-800 mb-4">{alertDlg.message}</p>
            <div className="flex justify-end">
              <button className="btn-industrial btn-industrial--secondary px-4 py-2 rounded" onClick={closeAlert}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      <h1 className="section-title text-4xl font-bold mb-8 text-center">Garages</h1>
      <div className="flex flex-col gap-6">
        {garages.map(garage => {
          const isFree = unlockedCount === 0 && !garage.unlocked;
          const list = busesByGarage[String(garage.id)] || [];
          return (
            <div
              key={garage.id}
              className="panel bg-white p-6 rounded-2xl shadow border-4 border-blue-800 flex flex-col gap-4"
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                <div>
                  <h2 className="text-2xl font-bold text-blue-900">{garage.name}</h2>
                  <div className="chips mt-2">
                    <span className="chip chip--meta">📍 {garage.location}</span>
                    {!garage.unlocked && (
                      <span className="chip chip--warn">
                        Unlock: {isFree ? "Free (first garage)" : "100000 💰"}
                      </span>
                    )}
                    <span className={`badge-status ${garage.unlocked ? "is-ok" : "is-idle"}`}>
                      {garage.unlocked ? "Unlocked" : "Locked"}
                    </span>
                  </div>
                </div>

                <div className="flex flex-col items-end gap-2">
                  {garage.unlocked ? (
                    <span className="text-sm text-gray-700">
                      Buses stored: <strong>{list.length}</strong>
                    </span>
                  ) : (
                    <button
                      className={`btn-industrial text-black px-4 py-2 rounded hover:font-bold ${
                        isFree ? "btn-industrial--primary" : "btn-industrial--secondary"
                      }`}
                      onClick={() =>
                        openConfirm(
                          "Unlock garage",
                          isFree ? "Unlock this garage for free?" : "Unlock this garage for 100000 💰?",
                          () => handleUnlock(garage.id, 100000)
                        )
                      }
                    >
                      {isFree ? "Unlock for Free" : "Unlock"}
                    </button>
                  )}
                </div>
              </div>

              {garage.unlocked && (
                <div className="border-t pt-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="bus-meta-label text-xs text-gray-600 font-semibold">Buses stored here</span>
                    <span className="text-xs font-semibold text-blue-900">{list.length}</span>
                  </div>
                  {list.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {list.map(bus => {
                        const label = displayStatus(bus.status);
                        const cls =
                          label === "Active"
                            ? "bg-green-100 text-green-800 border border-green-300"
                            : label === "Broken"
                              ? "bg-red-100 text-red-800 border border-red-300"
                              : "bg-gray-100 text-gray-800 border border-gray-300";
                        return (
                          <div
                            key={bus.plate}
                            className="bg-white border-2 border-blue-200 rounded-xl p-3 flex items-center justify-between shadow-sm"
                          >
                            <div className="flex flex-col">
                              <span className="bus-plate">{bus.plate}</span>
                              <span className="text-xs text-gray-600 mt-1">{bus.type}</span>
                            </div>
                            <div className="text-right text-xs text-gray-700">
                              <div className="chips justify-end">
                                <span className="chip chip--meta">KM {bus.km?.toLocaleString?.() || bus.km}</span>
                                <span className={`px-2 py-0.5 rounded ${cls}`}>{label}</span>
                                {bus.line && bus.line !== '-' ? (
                                  <span className="line-plate">{bus.line}</span>
                                ) : (
                                  <span className="text-gray-500">-</span>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="text-sm text-gray-500">No buses in this garage.</div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}