import { useEffect, useState } from "react";
import axios from "axios";

export default function Lines() {
  const [lines, setLines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [schedulesByLine, setSchedulesByLine] = useState({});
  const [winnersByLine, setWinnersByLine] = useState({});
  const [garagesMap, setGaragesMap] = useState({});
  const frameTagClass = (f) => {
    const k = String(f || "");
    if (k === "morning") return "frame-tag frame--morning";
    if (k === "midday") return "frame-tag frame--midday";
    if (k === "afternoon") return "frame-tag frame--afternoon";
    if (k === "evening") return "frame-tag frame--evening";
    if (k === "night") return "frame-tag frame--night";
    return "frame-tag";
  };
  const hhmmToMin = (s) => {
    if (!s) return null;
    const [h, m] = s.split(":").map(Number);
    if (Number.isNaN(h) || Number.isNaN(m)) return null;
    return (h === 24 && m === 0) ? 24 * 60 : (h * 60 + m);
  };
  const isNowInWindow = (start, end) => {
    const now = new Date();
    const nowMin = now.getHours() * 60 + now.getMinutes();
    const s = hhmmToMin(start);
    const e = hhmmToMin(end);
    if (s == null || e == null) return false;
    if (e <= s) {
      return nowMin >= s || nowMin < e;
    }
    return s <= nowMin && nowMin < e;
  };

  useEffect(() => {
    axios.get("http://localhost:5000/lines", { withCredentials: true })
      .then(res => setLines(res.data))
      .catch(() => setLines([]))
      .finally(() => setLoading(false));


    axios.get("http://localhost:5000/garages", { withCredentials: true })
      .then(res => {
        const map = {};
        (res.data || []).forEach(g => { map[g.id] = g.name || `Garage #${g.id}`; });
        setGaragesMap(map);
      })
      .catch(() => setGaragesMap({}));
    axios.get("http://localhost:5000/lines/winners", { withCredentials: true })
      .then(res => {
        const winners = {};
        res.data.forEach(w => {
          winners[w.line_name] = w;
        });
        setWinnersByLine(winners);
      });

    axios.get("http://localhost:5000/lines", { withCredentials: true })
      .then(res => {
        res.data.forEach(line => {
          axios.get(`http://localhost:5000/lines/${line.name}/schedules`, { withCredentials: true })
            .then(schRes => {
              setSchedulesByLine(prev => ({
                ...prev,
                [line.name]: schRes.data
              }));
            });
        });
      });
  }, []);

  if (loading) return <div className="text-center mt-20">Loading lines...</div>;

  return (
    <div className="max-w-4xl mx-auto mt-8">
      <h1 className="section-title text-4xl font-bold mb-8 text-center">Service Lines</h1>
      <div className="flex flex-col gap-6">
        {lines.map(line => {
          const allSchedules = schedulesByLine[line.name] || [];
          const activeNow = allSchedules.filter(s => s.status === "active" && isNowInWindow(s.start_time, s.end_time));
          const activeAll = allSchedules.filter(s => s.status === "active");
          const winnerNow = [...activeNow].sort((a, b) => {
            const fa = parseInt(a.frequency, 10); const fb = parseInt(b.frequency, 10);
            if (fb !== fa) return fb - fa;
            const ba = parseInt(a.bid_price, 10); const bb = parseInt(b.bid_price, 10);
            return ba - bb;
          })[0];

          return (
            <div
              key={line.name}
              className={`p-6 rounded-2xl shadow-lg border-4 ${
                winnerNow ? "border-green-600 bg-green-100" : "border-red-600 bg-red-100"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <h2 className="text-xl font-semibold">
                  <span className="line-plate">{line.name}</span>
                </h2>
                {winnerNow ? (
                  <div className="font-bold text-green-800">Currently serviced by {winnerNow.username}</div>
                ) : (
                  <div className="font-bold text-red-800">Currently out of service</div>
                )}
              </div>

              <div className="chips mt-2">
                <span className="chip chip--meta">
                  🏭 - {garagesMap[line.provider_garage_id] ?? `#${line.provider_garage_id}`}
                </span>
                <span className="chip chip--meta">⏱️ Line time - {line.travel_time_line} min</span>
              </div>

              <div className="mt-3 text-sm text-gray-800">
                {winnerNow && (
                  <div className="flex flex-col gap-1">
                    <div className="chips">
                      <span className="chip chip--meta">👤 - {winnerNow.username}</span>
                      <span className="chip chip--meta">🔁 - Every {winnerNow.frequency} min</span>
                      <span className="chip chip--meta">🪙 Bid - {winnerNow.bid_price}</span>
                      <span className={frameTagClass(winnerNow.frame)}>{winnerNow.frame || "-"}</span>
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-4">
                <h3 className="font-semibold mb-1">Schedules in service</h3>
                {activeAll.length === 0 ? (
                  <span className="text-gray-500">No active schedules.</span>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {activeAll.map(sch => (
                      <div
                        key={sch.id}
                        className="p-3 rounded-xl border-2 border-green-600 bg-green-50 shadow-sm"
                      >
                        <div className="font-bold text-blue-900">{sch.username}</div>
                        <div className="chips mt-1">
                          <span className="chip chip--meta">🔁 {sch.frequency} min</span>
                          <span className="chip chip--meta">🪙 {sch.bid_price}</span>
                          <span className={frameTagClass(sch.frame)}>{sch.frame || "-"}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}