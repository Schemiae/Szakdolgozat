import { useState, useEffect } from "react";
import axios from "axios";

function parseTimeToSeconds(timeStr) {
  const [hh, mm, ss] = timeStr.split(":").map(Number);
  return hh * 3600 + mm * 60 + ss;
}

function getCurrentTimeString() {
  const now = new Date();
  const yyyy = now.getFullYear();
  const MM = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  const ss = String(now.getSeconds()).padStart(2, "0");
  return `${yyyy}.${MM}.${dd} - ${hh}:${mm}:${ss}`;
}

export default function Issues({ balance, fetchBalance }) {
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [repairs, setRepairs] = useState({});
  const [now, setNow] = useState(Date.now());
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    bus: "",
    time: "",
    repair_time: "",
    repair_cost: "",
    description: ""
  });
  const [submitting, setSubmitting] = useState(false);
  const [userBuses, setUserBuses] = useState([]);

  const [confirm, setConfirm] = useState({ open: false, title: "", message: "", onConfirm: null });
  const openConfirm = (title, message, onConfirm) => setConfirm({ open: true, title, message, onConfirm });
  const closeConfirm = () => setConfirm({ open: false, title: "", message: "", onConfirm: null });

  const [alertDlg, setAlertDlg] = useState({ open: false, title: "", message: "" });
  const openAlert = (title, message) => setAlertDlg({ open: true, title, message });
  const closeAlert = () => setAlertDlg({ open: false, title: "", message: "" });

  useEffect(() => {
    const savedRepairs = localStorage.getItem("repairs");
    if (savedRepairs) {
      try {
        const parsed = JSON.parse(savedRepairs);
        const migrated = Object.fromEntries(
          Object.entries(parsed).map(([id, v]) => {
            return [
              id,
              typeof v === "number" && v < 1e12 ? Date.now() + v * 1000 : v
            ];
          })
        );
        setRepairs(migrated);
        localStorage.setItem("repairs", JSON.stringify(migrated));
      } catch {}
    }
  }, []);

  useEffect(() => {
    axios.get("http://localhost:5000/buszok", { withCredentials: true })
      .then(res => setUserBuses(res.data))
      .catch(() => setUserBuses([]));
  }, []);

  useEffect(() => {
    axios.get("http://localhost:5000/hibak", { withCredentials: true })
      .then((res) => setIssues(res.data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
    fetchBalance();
  }, [fetchBalance]);

  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const toRemove = [];
    Object.entries(repairs).forEach(([id, endsAt]) => {
      if (Date.now() >= endsAt) {
        toRemove.push(id);
      }
    });
    if (toRemove.length) {
      toRemove.forEach((id) => handleRemove(Number(id)));
      setRepairs((prev) => {
        const updated = { ...prev };
        toRemove.forEach((id) => delete updated[id]);
        localStorage.setItem("repairs", JSON.stringify(updated));
        return updated;
      });
    }
  }, [now, repairs]);

  const handleRepair = (issue) => {
    const required = Number(issue.repair_cost) || 0;
    const available = Number(balance) || 0;
    if (available < required) {
      openAlert(
        "Insufficient balance",
        `Required: ${required.toLocaleString()} 💰, Available: ${available.toLocaleString()} 💰`
      );
      return;
    }
    if (repairs[issue.id]) return;
    axios.post("http://localhost:5000/user/deduct_balance", {
      amount: issue.repair_cost
    }, { withCredentials: true })
      .then(() => {
        fetchBalance();
        const seconds = parseTimeToSeconds(issue.repair_time);
        const endsAt = Date.now() + seconds * 1000;
        setRepairs(prev => {
          const updated = { ...prev, [issue.id]: endsAt };
          localStorage.setItem("repairs", JSON.stringify(updated));
          return updated;
        });
      })
      .catch(() => openAlert("Error", "Failed to deduct balance!"));
  };

  const handleCancelRepair = (id) => {
    if (!repairs[id]) return;
    setRepairs(prev => {
      const updated = { ...prev };
      delete updated[id];
      localStorage.setItem("repairs", JSON.stringify(updated));
      return updated;
    });
  };

  const handleRemove = (id) => {
    axios.delete(`http://localhost:5000/hiba/${id}`, { withCredentials: true })
      .then(() => {
        setIssues((prev) => prev.filter((i) => i.id !== id));
      })
      .catch(() => openAlert("Error", "Failed to remove issue!"));
  };

  if (loading) return <div className="text-center mt-20">Loading issues...</div>;

  return (
    <div className="max-w-5xl mx-auto mt-8">
      {confirm.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="panel bg-white border-4 border-blue-800 rounded-2xl p-6 w-full max-w-md shadow-lg">
            <h3 className="text-xl font-bold text-blue-900 mb-2">{confirm.title}</h3>
            <p className="text-gray-800 mb-4">{confirm.message}</p>
            <div className="flex justify-end gap-2">
              <button className="btn-industrial btn-industrial--secondary px-4 py-2 rounded" onClick={closeConfirm}>Cancel</button>
              <button className="btn-industrial btn-industrial--primary px-4 py-2 rounded" onClick={() => { confirm.onConfirm && confirm.onConfirm(); closeConfirm(); }}>
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
              <button className="btn-industrial btn-industrial--secondary px-4 py-2 rounded" onClick={closeAlert}>Close</button>
            </div>
          </div>
        </div>
      )}

      <h1 className="section-title text-4xl font-bold mb-8 text-center">Your Bus Issues</h1>

      <div className="mb-8 flex flex-col items-center">
        <button
          className={`mb-4 px-6 py-2 rounded-lg font-semibold shadow transition-all btn-industrial ${
            showForm ? "btn-industrial--primary" : "btn-industrial--secondary hover:bg-blue-300"
          }`}
          onClick={() => {
            if (!showForm) setForm(f => ({ ...f, time: getCurrentTimeString() }));
            setShowForm(f => !f);
          }}
        >
          {showForm ? "Hide Issue Form" : "Report New Issue"}
        </button>

        {showForm && (
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              setSubmitting(true);
              try {
                await axios.post("http://localhost:5000/hiba", form, { withCredentials: true });
                setShowForm(false);
                setForm({ bus: "", time: "", repair_time: "", repair_cost: "", description: "" });
                axios.get("http://localhost:5000/hibak", { withCredentials: true })
                  .then((res) => setIssues(res.data));
              } catch (err) {
                openAlert("Error", "Failed to report issue");
              }
              setSubmitting(false);
            }}
            className="panel bg-white border-4 border-blue-800 rounded-lg p-6 w-full max-w-lg shadow-lg flex flex-col gap-3"
          >
            <select
              className="input-industrial border p-2 rounded"
              value={form.bus}
              onChange={e => setForm(f => ({ ...f, bus: e.target.value }))}
              required
            >
              <option value="" disabled>Select Bus Plate</option>
              {userBuses.map(bus => (
                <option key={bus.plate} value={bus.plate}>
                  {bus.plate}
                </option>
              ))}
            </select>
            <input
              className="input-industrial border p-2 rounded"
              placeholder="Reported Time (YYYY-MM-DD HH:MM:SS)"
              value={form.time}
              readOnly
              required
            />
            <input
              className="input-industrial border p-2 rounded"
              placeholder="Repair Time (hh:mm:ss)"
              value={form.repair_time}
              onChange={e => setForm(f => ({ ...f, repair_time: e.target.value }))}
              required
            />
            <input
              className="input-industrial border p-2 rounded"
              placeholder="Repair Cost"
              type="number"
              value={form.repair_cost}
              onChange={e => setForm(f => ({ ...f, repair_cost: parseInt(e.target.value) }))}
              required
            />
            <textarea
              className="input-industrial border p-2 rounded"
              placeholder="Description"
              value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              required
            />
            <button
              type="submit"
              className="btn-industrial btn-industrial--primary text-black px-4 py-2 rounded hover:font-bold"
              disabled={submitting}
            >
              {submitting ? "Reporting..." : "Confirm"}
            </button>
          </form>
        )}
      </div>

      <div className="flex flex-col gap-4">
        {issues.map((issue) => {
          const isRepairing = !!repairs[issue.id];
          return (
            <div
              key={issue.id}
              className="panel bg-white p-4 rounded-2xl shadow border-4 border-blue-800 flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="bus-plate">{issue.bus}</span>
                  <span className={`badge-status ${isRepairing ? "is-ok" : "is-broken"}`}>
                    {isRepairing ? "Repairing" : "Open"}
                  </span>
                </div>
                <div className="chips">
                  <span className="chip chip--meta">📅 Reported: {issue.time}</span>
                  <span className="chip chip--meta">⏱️ Repair: {issue.repair_time}</span>
                  <span className="chip chip--warn">💰 Cost: {issue.repair_cost}</span>
                </div>
                {issue.description && (
                  <div className="mt-2 text-sm text-gray-800">
                    <span className="bus-meta-label">Description:</span> {issue.description}
                  </div>
                )}
              </div>

              <div className="flex flex-col items-end gap-2 min-w-[180px]">
                {isRepairing ? (
                  <>
                    <span className="badge-status is-ok">
                      {Math.max(0, Math.ceil((repairs[issue.id] - now) / 1000))}s remaining
                    </span>
                    <button
                      className="btn-industrial btn-industrial--danger text-black px-4 py-2 rounded"
                      onClick={() =>
                        openConfirm("Cancel repair", "Cancel this repair?", () => handleCancelRepair(issue.id))
                      }
                    >
                      Cancel
                    </button>
                  </>
                ) : (
                  <button
                    className="btn-industrial btn-industrial--primary text-black px-4 py-2 rounded"
                    onClick={() =>
                      openConfirm(
                        "Start repair",
                        `Repair this issue for ${issue.repair_cost} 💰?`,
                        () => handleRepair(issue)
                      )
                    }
                    disabled={!!repairs[issue.id]}
                  >
                    Repair
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}