import { useEffect, useState } from "react";
import axios from "axios";

export default function Schedules() {
  const [schedules, setSchedules] = useState([]);
  const [selectedSchedule, setSelectedSchedule] = useState(null);
  const [assignments, setAssignments] = useState([]);
  const [assignmentPlan, setAssignmentPlan] = useState(null);
  const [userBuses, setUserBuses] = useState([]);
  const [manualAssignments, setManualAssignments] = useState({});
  const [lines, setLines] = useState([]);
  const [garages, setGarages] = useState([]);
  const [bidCap, setBidCap] = useState(null);
  const [form, setForm] = useState({
    line_name: "",
    start_time: "",
    end_time: "",
    frequency: 15,
    bid_price: 0
  });
  const [showForm, setShowForm] = useState(false);

  const [confirm, setConfirm] = useState({ open: false, title: "", message: "", onConfirm: null });
  const openConfirm = (title, message, onConfirm) => setConfirm({ open: true, title, message, onConfirm });
  const closeConfirm = () => setConfirm({ open: false, title: "", message: "", onConfirm: null });

  const [alertDlg, setAlertDlg] = useState({ open: false, title: "", message: "" });
  const openAlert = (title, message) => setAlertDlg({ open: true, title, message });
  const closeAlert = () => setAlertDlg({ open: false, title: "", message: "" });

  const selectedLine = lines.find(l => l.name === form.line_name);
  const providerGarageId = selectedLine?.provider_garage_id ?? null;
  const providerGarageName = providerGarageId
    ? (garages.find(g => String(g.id) === String(providerGarageId))?.name || `#${providerGarageId}`)
    : "-";
  const userHasProviderGarage = providerGarageId
    ? garages.some(g => String(g.id) === String(providerGarageId) && g.unlocked)
    : false;

  useEffect(() => {
    if (form.frequency) fetchBidCap(form.frequency, form.frame);
  }, [form.frequency, form.frame]);

  useEffect(() => {
    axios.get("http://localhost:5000/schedules", { withCredentials: true })
      .then(res => setSchedules(res.data));
    axios.get("http://localhost:5000/buszok", { withCredentials: true })
      .then(res => setUserBuses(res.data));
    axios.get("http://localhost:5000/lines", { withCredentials: true })
      .then(res => setLines(res.data));
    axios.get("http://localhost:5000/garages", { withCredentials: true })
      .then(res => setGarages(res.data));
  }, []);

  const garageNameById = (id) => {
    if (!id) return "-";
    return garages.find(g => String(g.id) === String(id))?.name || `#${id}`;
  };

  const statusBadgeClass = (status) => {
    if (status === "active") return "bg-green-100 text-green-900 border-green-600";
    if (status === "paused") return "bg-yellow-100 text-yellow-900 border-yellow-600";
    return "bg-gray-100 text-gray-800 border-gray-400";
  };

  const scheduleSideClass = (status) => {
    if (status === "active") return "schedule-card schedule-card--active";
    if (status === "paused") return "schedule-card schedule-card--paused";
    return "schedule-card schedule-card--pending";
  };

  const frameTagClass = (f) => {
    const k = String(f || "");
    if (k === "morning") return "frame-tag frame--morning";
    if (k === "midday") return "frame-tag frame--midday";
    if (k === "afternoon") return "frame-tag frame--afternoon";
    if (k === "evening") return "frame-tag frame--evening";
    if (k === "night") return "frame-tag frame--night";
    return "frame-tag";
  };

  const handleSelectSchedule = (id) => {
    if (selectedSchedule === id) {
      setSelectedSchedule(null);
      setAssignments([]);
      setAssignmentPlan(null);
      setManualAssignments({});
      return;
    }
    setSelectedSchedule(id);
    axios.get(`http://localhost:5000/schedules/${id}/assignments`, { withCredentials: true })
      .then(res => {
        const data = res.data;
        let initialAssignments = {};
        if (data && Array.isArray(data.assignments)) {
          setAssignments(data.assignments);
          setAssignmentPlan(data);
          data.assignments.forEach((block, idx) => {
            if (block.assigned_bus) initialAssignments[idx] = block.assigned_bus;
          });
        } else if (Array.isArray(data)) {
          setAssignments(data);
          setAssignmentPlan(null);
        } else {
          setAssignments([]);
          setAssignmentPlan(null);
        }
        setManualAssignments(initialAssignments);
      })
      .catch(() => {
        setAssignments([]);
        setAssignmentPlan(null);
        setManualAssignments({});
      });
  };

  const fetchBidCap = (freq, frame) => {
    if (!freq) return;
    axios.get("http://localhost:5000/schedules/bid-cap", {
      params: { frequency: parseInt(freq, 10), frame },
      withCredentials: true
    })
    .then(res => setBidCap(res.data.cap))
    .catch(err => {
      console.error("Failed to fetch bid cap", err);
      setBidCap(null);
    });
  };

  const handleManualAssign = (blockIdx, busRendszam) => {
    setManualAssignments(prev => ({ ...prev, [blockIdx]: busRendszam }));
  };

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setForm(f => ({ ...f, [name]: value }));
    if (name === "frequency" || name === "frame") {
      const next = { ...form, [name]: value };
      fetchBidCap(next.frequency, next.frame);
    }
  };

  const handleCreateSchedule = (e) => {
    e.preventDefault();
    if (!userHasProviderGarage) {
      alert("You must unlock the provider garage for this line first.");
      return;
    }
    if (bidCap != null && parseFloat(form.bid_price) > bidCap) {
      alert(`Bid exceeds allowed cap (${bidCap}). Lower your bid or increase frequency.`);
      return;
    }
    const payload = {
      line_name: form.line_name,
      frame: form.frame,
      frequency: parseInt(form.frequency, 10),
      bid_price: parseInt(form.bid_price, 10)
    };
    axios.post("http://localhost:5000/schedules", payload, { withCredentials: true })
      .then(res => {
        axios.get("http://localhost:5000/schedules", { withCredentials: true })
          .then(res => setSchedules(res.data));
        setShowForm(false);
        setForm({ line_name: "", frequency: 15, bid_price: 0, frame: "" });
      })
      .catch(err => openAlert("Error", err.response?.data?.error || "Failed to create schedule"));
  };

  const handleSaveAssignments = () => {
    if (!selectedSchedule) return;
    const assignmentsToSend = {};
    assignments.forEach((block, idx) => {
      if (manualAssignments[idx]) {
        assignmentsToSend[idx] = manualAssignments[idx];
      }
    });

    const vals = Object.values(assignmentsToSend).filter(Boolean);
    const dup = vals.find((v, i) => vals.indexOf(v) !== i);
    if (dup) {
      alert(`Bus ${dup} is assigned to multiple blocks. Please choose unique buses.`);
      return;
    }

    axios.post(
      `http://localhost:5000/schedules/${selectedSchedule}/manual_assignments`,
      { assignments: assignmentsToSend },
      { withCredentials: true }
    )
    .then(res => {
      handleSelectSchedule(selectedSchedule);
      axios.get("http://localhost:5000/buszok", { withCredentials: true })
        .then(r => setUserBuses(r.data))
        .catch(() => {});
      axios.get("http://localhost:5000/schedules", { withCredentials: true })
        .then(r => setSchedules(r.data))
        .catch(() => {});
    })
    .catch(err => openAlert("Error", err.response?.data?.error || "Failed to save assignments"));
  };

  const selectedScheduleGarageId = (() => {
    const sch = schedules.find(s => s.id === selectedSchedule);
    return sch ? sch.garage_id : null;
  })();

  const selectedScheduleObj = schedules.find(s => s.id === selectedSchedule);

  return (
    <div className="max-w-5xl mx-auto mt-10">
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
              <button className="btn-industrial btn-industrial--secondary px-4 py-2 rounded" onClick={closeAlert}>Close</button>
            </div>
          </div>
        </div>
      )}

      <h1 className="section-title text-4xl font-bold mb-8 text-center">Schedules</h1>

      <div className="mb-8 flex flex-col items-center">
        <button
          className={`mb-4 px-6 py-2 rounded-lg font-semibold shadow transition-all btn-industrial ${
            showForm ? "btn-industrial--primary" : "btn-industrial--secondary hover:bg-blue-300"
          }`}
          onClick={() => setShowForm(f => !f)}
        >
          {showForm ? "Hide Create Schedule Form" : "Create New Schedule"}
        </button>
        {showForm && (
          <form onSubmit={handleCreateSchedule} className="panel bg-white border-2 border-blue-800 rounded-lg p-6 w-full max-w-lg shadow-lg flex flex-col gap-3">
            <select name="line_name" value={form.line_name} onChange={handleFormChange} required className="border p-2 rounded">
              <option value="">Select Line</option>
              {lines.map(line => (
                <option key={line.name} value={line.name}>{line.name}</option>
              ))}
            </select>
            <div className={`border p-2 rounded ${userHasProviderGarage ? "bg-green-50" : "bg-red-50"}`}>
              <div className="text-sm text-gray-600">Provider Garage</div>
              <div className="flex items-center justify-between">
                <div className="font-semibold">{providerGarageName}</div>
                <span className={`text-sm font-bold px-2 py-1 rounded ${
                  userHasProviderGarage
                    ? "bg-green-200 text-green-900"
                    : "bg-red-200 text-red-900"
                }`}>
                  {userHasProviderGarage ? "✓ Unlocked" : "🔒 Locked"}
                </span>
              </div>
            </div>
            <input name="bid_price" type="number" min="0" max={bidCap ?? undefined} value={form.bid_price || ""} onChange={handleFormChange} required className="border p-2 rounded" placeholder="Bid price (money per slot)"/>
            {bidCap != null && (
              <div className="text-sm text-gray-600">
                Max allowed bid for this frequency and frame: <strong>{bidCap}</strong>
              </div>
            )}
            <select name="frame" value={form.frame || ""} onChange={handleFormChange} required className="border p-2 rounded">
              <option value="">Select Frame</option>
              <option value="morning">morning (04:00-08:00)</option>
              <option value="midday">midday (08:00-12:00)</option>
              <option value="afternoon">afternoon (12:00-16:00)</option>
              <option value="evening">evening (16:00-20:00)</option>
              <option value="night">night (20:00-24:00)</option>
            </select>
            <input name="frequency" type="number" min="1" value={form.frequency} onChange={handleFormChange} required className="border p-2 rounded" placeholder="Frequency (minutes)" />
            <button 
              type="submit" 
              disabled={!userHasProviderGarage}
              className={`btn-industrial px-4 py-2 rounded hover:font-bold transition ${
                userHasProviderGarage ? "btn-industrial--primary" : "btn-industrial--secondary cursor-not-allowed"
              }`}
            >
              {userHasProviderGarage ? "Create Schedule" : "Unlock Garage First"}
            </button>
          </form>
        )}
      </div>

      <h2 className="section-title text-2xl font-semibold mb-4 text-center">Your Schedules</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
        { schedules.map(sch => {
          const providerName = garageNameById(sch.garage_id);
          return (
            <div key={sch.id} className="relative panel rounded-xl">
              <button
                className={`w-full text-left px-6 py-5 rounded-xl shadow-lg border-4 transition-all font-semibold text-lg ${scheduleSideClass(sch.status)} ${
                  sch.status === "active"
                    ? "bg-green-50 text-green-900 border-green-600"
                    : selectedSchedule === sch.id
                      ? "bg-blue-600 text-black border-blue-800"
                      : "bg-blue-50 text-blue-900 border-blue-300 hover:bg-blue-100"
                } ${selectedSchedule === sch.id ? "ring-2 ring-offset-2 ring-blue-600" : ""}`}
                onClick={() => handleSelectSchedule(sch.id)}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex flex-col gap-1">
                    <span className="font-bold text-xl flex items-center gap-2">
                      <span className="line-plate">{sch.line_name}</span>
                      <span className={frameTagClass(sch.frame)}>{sch.frame || "-"}</span>
                    </span>
                    <div className="chips mt-1">
                      <span className="chip chip--meta">⏰ {sch.start_time} - {sch.end_time}</span>
                      <span className="chip chip--meta">🔁 Every {sch.frequency} min</span>
                      <span className="chip chip--meta">🪙 {sch.bid_price}</span>
                      <span className="chip chip--meta">🏭 {providerName}</span>
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded border text-xs ${statusBadgeClass(sch.status)}`}>{sch.status}</span>
                </div>
              </button>
              <button
                className="absolute top-2 right-2 btn-industrial btn-industrial--danger text-black px-2 py-1 rounded"
                onClick={e => {
                  e.stopPropagation();
                  openConfirm(
                    "Delete schedule",
                    "Are you sure you want to delete this schedule?",
                    () => {
                      axios
                        .delete(`http://localhost:5000/schedules/${sch.id}`, { withCredentials: true })
                        .then(() => setSchedules(schedules => schedules.filter(s => s.id !== sch.id)))
                        .catch(() => openAlert("Error", "Failed to delete schedule"));
                    }
                  );
                }}
              >
                Delete
              </button>
            </div>
          );
        }) }
      </div>

      {selectedScheduleObj && (
        <div className="mb-6 p-4 rounded-xl border-4 border-blue-800 bg-white panel">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-xl font-bold text-blue-900 flex items-center gap-2">
                <span className="line-plate">{selectedScheduleObj.line_name}</span>
                <span className={frameTagClass(selectedScheduleObj.frame)}>{selectedScheduleObj.frame || "-"}</span>
              </div>
              <div className="chips mt-2">
                <span className="chip chip--meta">⏰ {selectedScheduleObj.start_time} - {selectedScheduleObj.end_time}</span>
                <span className="chip chip--meta">🔁 Every {selectedScheduleObj.frequency} min</span>
                <span className="chip chip--meta">🪙 {selectedScheduleObj.bid_price}</span>
                <span className="chip chip--meta">🏭 {garageNameById(selectedScheduleObj.garage_id)}</span>
              </div>
            </div>
            <span className={`px-2 py-1 rounded border text-xs ${statusBadgeClass(selectedScheduleObj.status)}`}>{selectedScheduleObj.status}</span>
          </div>
          {assignmentPlan && (
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-800">
              <div><strong>Travel times:</strong> garage {assignmentPlan.travel_time_garage} min, line {assignmentPlan.travel_time_line} min</div>
              <div><strong>Buses used:</strong> {assignmentPlan.buses_used}</div>
              <div className="md:col-span-2 chips"><strong>All slots:</strong>{" "}{assignmentPlan.slots?.map((s, i) => (<span key={i} className="chip chip--slot">{String(s)}</span>))}</div>
            </div>
          )}
        </div>
      )}

      {assignments.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="section-title text-xl font-semibold">Bus Assignments</h2>
            <div className="text-sm text-gray-600">
              {selectedScheduleGarageId ? (
                <>Only buses from garage <strong>{garageNameById(selectedScheduleGarageId)}</strong> in Standby status are eligible.</>
              ) : (
                <>Any bus in Standby status is eligible.</>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-4">
            {assignments.map((block, idx) => {
              const busNumber = block.bus_id ?? block.bus_number ?? (idx + 1);
              const slots = (block.departures ?? block.slots ?? []).map(String);
              const workStart = block.duty_start ?? block.work_start ?? "";
              const workEnd = block.duty_end ?? block.work_end ?? "";

              const breaksList = Array.isArray(block.breaks) ? block.breaks : null;
              const singleBreak = !breaksList && (block.break_start || block.break_end) ? [{ start: block.break_start, end: block.break_end }] : [];

              const usedByOthers = new Set(
                Object.entries(manualAssignments)
                  .filter(([i, v]) => v && parseInt(i, 10) !== idx)
                  .map(([, v]) => v)
              );

              const eligibleBuses = userBuses.filter(bus => bus.status === "KT" && (
                selectedScheduleGarageId == null || String(bus.garage) === String(selectedScheduleGarageId)
              ));

              return (
                <div key={idx} className="bg-white text-black p-4 rounded shadow border-4 border-blue-800 panel--light panel">
                  <div className="flex items-center justify-between">
                    <div className="flex flex-col gap-1">
                      <strong className="text-blue-800">Block #{busNumber}</strong>
                      <div className="chips">
                        <span className="chip chip--meta">🕒 {workStart} - {workEnd}</span>
                        {slots.map((s, i) => (<span key={i} className="chip chip--slot">⏱️ {s}</span>))}
                        {(breaksList && breaksList.length > 0 ? breaksList : singleBreak).map((br, i) => (
                          <span key={i} className="chip chip--break">☕ {br.start} - {br.end}</span>
                        ))}
                      </div>
                    </div>
                    <div className="text-right text-sm text-gray-700">
                      <div className="chip chip--meta">🚌 Eligible: <strong>{eligibleBuses.length}</strong></div>
                      {eligibleBuses.length === 0 && (
                        <div className="chip chip--warn">No eligible buses</div>
                      )}
                    </div>
                  </div>
                  <div className="mt-3 flex items-center gap-2">
                    <label className="mr-2 font-semibold text-blue-800">Assign Bus:</label>
                    <select
                      value={manualAssignments[idx] || ""}
                      onChange={e => handleManualAssign(idx, e.target.value)}
                      className="input-industrial border p-1 rounded text-black"
                    >
                      <option value="">None</option>
                      {eligibleBuses.map(bus => (
                        <option key={bus.plate} value={bus.plate} disabled={usedByOthers.has(bus.plate)}>
                          {bus.plate} ({bus.type}){usedByOthers.has(bus.plate) ? " — already used" : ""}
                        </option>
                      ))}
                    </select>
                    {manualAssignments[idx] && (
                      <>
                        <span className="ml-2 bus-plate">{manualAssignments[idx]}</span>
                        <button className="ml-2 btn-industrial btn-industrial--danger px-2 py-1 rounded" onClick={() => handleManualAssign(idx, "")} type="button">Remove</button>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="flex items-center justify-between mt-6">
            <div className="text-sm text-gray-600">Tip: Assign each Standby bus at most once per schedule.</div>
            <button className="btn-industrial btn-industrial--primary px-6 py-3 rounded-xl font-bold shadow" onClick={handleSaveAssignments}>Save Manual Assignments</button>
          </div>
        </div>
      )}
    </div>
  );
}