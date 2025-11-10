import { useState, useEffect } from "react";
import axios from "axios";

export default function Market({ onPurchase }) {
  const [buses, setBuses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [listings, setListings] = useState([]);
  const [models, setModels] = useState([]);
  const [garages, setGarages] = useState([]);
  const [form, setForm] = useState({ model_key: "", rendszam: "", leiras: "", garazs: "" });
  const [username, setUsername] = useState(null);
  const [myBuses, setMyBuses] = useState([]);
  const [listForm, setListForm] = useState({ rendszam: "", price: "" });
  const [targetGarageByListing, setTargetGarageByListing] = useState({});
  const [targetGarageByBus, setTargetGarageByBus] = useState({});
  const [issuesByPlate, setIssuesByPlate] = useState({});
  const selectedModel = models.find(m => m.key === form.model_key);
  const modelPrice = selectedModel ? selectedModel.price : null;

  const [showBuyNew, setShowBuyNew] = useState(true);
  const [showCreateListing, setShowCreateListing] = useState(true);

  const [confirm, setConfirm] = useState({
    open: false,
    title: "",
    message: "",
    onConfirm: null,
  });
  const openConfirm = (title, message, onConfirm) => setConfirm({ open: true, title, message, onConfirm });
  const closeConfirm = () => setConfirm({ open: false, title: "", message: "", onConfirm: null });

  const [alertDlg, setAlertDlg] = useState({ open: false, title: "", message: "" });
  const openAlert = (title, message) => setAlertDlg({ open: true, title, message });
  const closeAlert = () => setAlertDlg({ open: false, title: "", message: "" });

  useEffect(() => {
    axios.get("http://localhost:5000/session", { withCredentials: true })
      .then(res => setUsername(res.data?.username || null))
      .catch(() => setUsername(null));

    axios.get("http://localhost:5000/market/listings", { withCredentials: true })
      .then(res => setListings(res.data))
      .catch(() => setListings([]));

    axios.get("http://localhost:5000/market", { withCredentials: true })
      .then((res) => setBuses(res.data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));

    axios.get("http://localhost:5000/market/models", { withCredentials: true })
      .then(res => setModels(res.data))
      .catch(() => setModels([]));

    axios.get("http://localhost:5000/garages", { withCredentials: true })
      .then(res => setGarages(res.data))
      .catch(() => setGarages([]));

    axios.get("http://localhost:5000/buszok", { withCredentials: true })
      .then(res => setMyBuses(res.data || []))
      .catch(() => setMyBuses([]));

    axios.get("http://localhost:5000/hibak/all", { withCredentials: true })
      .then(res => {
        const list = Array.isArray(res.data) ? res.data : [];
        const grouped = list.reduce((acc, it) => {
          const plate = it.bus || it.busz || it.rendszam || it.plate;
          if (!plate) return acc;
          (acc[plate] = acc[plate] || []).push(it);
          return acc;
        }, {});
        setIssuesByPlate(grouped);
      })
      .catch(() => setIssuesByPlate({}));
  }, []);

  const calculatePrice = (km) => {
    const basePrice = 100000;
    const minPrice = 10000;
    const maxKm = 500_000;
    const price = basePrice - (km / maxKm) * (basePrice - minPrice);
    return Math.round(Math.max(price, minPrice));
  };

  const handleBuyListing = (listingId) => {
    const raw = targetGarageByListing[listingId];
    const chosen = typeof raw === "number" && Number.isFinite(raw) ? raw : null;
    if (chosen == null) {
      alert("Please select a garage to store this bus.");
      return;
    }
    axios.post("http://localhost:5000/market/purchase", { listing_id: listingId, garage_id: chosen }, { withCredentials: true })
      .then(res => {
        onPurchase && onPurchase();
        setListings(ls => ls.filter(l => l.listing_id !== listingId));
      })
      .catch(err => openAlert("Error", err.response?.data?.error || "Purchase failed"));
  };

  const handleCancelListing = (listingId) => {
    axios.post("http://localhost:5000/market/cancel", { listing_id: listingId }, { withCredentials: true })
      .then(res => {
        setListings(ls => ls.filter(l => l.listing_id !== listingId));
      })
      .catch(err => openAlert("Error", err.response?.data?.error || "Cancel failed"));
  };

  const handleBuyUsed = (plate, price) => {
    const raw = targetGarageByBus[plate];
    const chosen = typeof raw === "number" && Number.isFinite(raw) ? raw : null;
    if (chosen == null) {
      alert("Please select a garage to store this bus.");
      return;
    }
    axios.post(
      "http://localhost:5000/market/buy",
      { rendszam: plate, price, garage_id: chosen },
      { withCredentials: true }
    )
    .then((res) => {
      onPurchase && onPurchase();
      setBuses((prev) => prev.filter((bus) => bus.plate !== plate));
    })
    .catch((err) => {
      console.error(err);
      openAlert("Error", err.response?.data?.error || "Purchase failed");
    });
  };

  const handleBuyNew = (e) => {
    e.preventDefault();
    if (!form.model_key || !form.rendszam || !form.leiras || !form.garazs) {
      alert("Please fill all fields");
      return;
    }
    const mdl = models.find(m => m.key === form.model_key);
    const price = mdl?.price;
    const payload = {
      model_key: form.model_key,
      rendszam: form.rendszam,
      leiras: form.leiras,
      garazs: parseInt(form.garazs, 10),
    };
    openConfirm(
      "Confirm Purchase",
      mdl ? `Buy new ${mdl.label} (${form.rendszam}) for ${price.toLocaleString()} 💰?` : `Buy new bus ${form.rendszam}?`,
      () => {
        axios.post("http://localhost:5000/market/purchase-new", payload, { withCredentials: true })
          .then(res => {
            onPurchase && onPurchase(res.data.new_balance);
            setForm({ model_key: "", rendszam: "", leiras: "", garazs: "" });
          })
          .catch(err => openAlert("Error", err.response?.data?.error || "Purchase failed"))
          .finally(() => closeConfirm());
      }
    );
  };

  const handleCreateListing = (e) => {
    e.preventDefault();
    const { rendszam, price } = listForm;
    const p = parseInt(price, 10);
    if (!rendszam || Number.isNaN(p) || p < 0) {
      alert("Select a bus and enter a valid price");
      return;
    }
    openConfirm(
      "Confirm Listing",
      `List ${rendszam} for ${p.toLocaleString()} 💰?`,
      () => {
        axios.post("http://localhost:5000/market/list", { rendszam, price: p }, { withCredentials: true })
          .then(res => {
            setListForm({ rendszam: "", price: "" });
            return axios.get("http://localhost:5000/market/listings", { withCredentials: true });
          })
          .then(resp => setListings(resp.data || []))
          .catch(err => openAlert("Error", err.response?.data?.error || "Failed to create listing"))
          .finally(() => closeConfirm());
      }
    );
  };

  if (loading) return <div className="text-center mt-10">Loading market...</div>;

  const unlockedGarages = (garages || []).filter(g => g.unlocked);
  const myListings = username ? listings.filter(l => l.seller_username === username) : [];
  const otherListings = username ? listings.filter(l => l.seller_username !== username) : listings;

  return (
    <div className="max-w-6xl mx-auto mt-8">
      {confirm.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="panel bg-white border-4 border-blue-800 rounded-2xl p-6 w-full max-w-md shadow-lg">
            <h3 className="text-xl font-bold text-blue-900 mb-2">{confirm.title}</h3>
            <p className="text-gray-800 mb-4">{confirm.message}</p>
            <div className="flex justify-end gap-2">
              <button className="btn-industrial btn-industrial--secondary px-4 py-2 rounded" onClick={closeConfirm}>Cancel</button>
              <button
                className="btn-industrial btn-industrial--primary px-4 py-2 rounded"
                onClick={() => confirm.onConfirm && confirm.onConfirm()}
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

      <h1 className="section-title text-4xl font-bold mb-8 text-center">Bus Market</h1>

      <div className="mb-10 grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
        <div className="panel bg-white border-4 border-green-700 p-6 rounded-2xl shadow-lg h-full">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-semibold">Buy New Bus</h2>
            <button
              className={`px-4 py-2 rounded-lg font-semibold shadow transition-all btn-industrial ${
                showBuyNew ? "btn-industrial--primary" : "btn-industrial--secondary hover:bg-blue-300"
              }`}
              onClick={() => setShowBuyNew(v => !v)}
            >
              {showBuyNew ? "Hide" : "Show"}
            </button>
          </div>
          {showBuyNew && (
            <>
              <form onSubmit={handleBuyNew} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <select
                  className="input-industrial border p-2 rounded"
                  value={form.model_key}
                  onChange={e => setForm(f => ({ ...f, model_key: e.target.value }))}
                  required
                >
                  <option value="">Select Model</option>
                  {models.map(m => (
                    <option key={m.key} value={m.key}>
                      {m.label}
                    </option>
                  ))}
                </select>
                <select
                  className="input-industrial border p-2 rounded"
                  value={form.garazs}
                  onChange={e => setForm(f => ({ ...f, garazs: e.target.value }))}
                  required
                >
                  <option value="">Select Garage</option>
                  {unlockedGarages.map(g => (
                    <option key={g.id} value={g.id}>{g.name || `Garage #${g.id}`}</option>
                  ))}
                </select>
                <input
                  className="input-industrial border p-2 rounded"
                  placeholder="License plate"
                  value={form.rendszam}
                  onChange={e => setForm(f => ({ ...f, rendszam: e.target.value }))}
                  required
                />
                <input
                  className="input-industrial border p-2 rounded"
                  placeholder="Description"
                  value={form.leiras}
                  onChange={e => setForm(f => ({ ...f, leiras: e.target.value }))}
                  required
                />
                <div className="md:col-span-2 text-gray-700">
                  {selectedModel ? (
                    <span>Price: <strong>{selectedModel.price.toLocaleString()} 💰</strong></span>
                  ) : <span>Select a model to see price</span>}
                </div>
                <button
                  type="submit"
                  className="md:col-span-2 btn-industrial btn-industrial--primary text-black px-5 py-2 rounded hover:font-bold"
                >
                  Buy New Bus
                </button>
              </form>
              {unlockedGarages.length === 0 && (
                <div className="text-sm text-red-600 mt-2">You have no unlocked garages. Unlock one first.</div>
              )}
            </>
          )}
        </div>

        <div className="panel bg-white border-4 border-yellow-700 p-6 rounded-2xl shadow-lg h-full">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-semibold">Create Listing</h2>
            <button
              className={`px-4 py-2 rounded-lg font-semibold shadow transition-all btn-industrial ${
                showCreateListing ? "btn-industrial--primary" : "btn-industrial--secondary hover:bg-blue-300"
              }`}
              onClick={() => setShowCreateListing(v => !v)}
            >
              {showCreateListing ? "Hide" : "Show"}
            </button>
          </div>
          {showCreateListing && (
            <>
              <form onSubmit={handleCreateListing} className="grid grid-cols-1 gap-3">
                <select
                  className="input-industrial border p-2 rounded"
                  value={listForm.rendszam}
                  onChange={e => setListForm(f => ({ ...f, rendszam: e.target.value }))}
                  required
                >
                  <option value="">Select Your Bus</option>
                  {myBuses.map(b => (
                    <option key={b.plate} value={b.plate}>
                      {b.plate} — {b.type}
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  min="0"
                  step="1"
                  className="input-industrial border p-2 rounded"
                  placeholder="Listing price"
                  value={listForm.price}
                  onChange={e => setListForm(f => ({ ...f, price: e.target.value }))}
                  required
                />
                <button
                  type="submit"
                  className="btn-industrial btn-industrial--primary text-black px-4 py-2 rounded hover:font-bold w-full"
                >
                  List Bus
                </button>
              </form>
            </>
          )}
        </div>
      </div>

      {username && myListings.length > 0 && (
        <div className="mb-10">
          <h2 className="section-title text-2xl font-semibold mb-4 text-center">Your Active Listings</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {myListings.map(l => {
              const plate = l.bus_plate;
              const issues = issuesByPlate[plate] || [];
              return (
                <div key={l.listing_id} className="bus-card bus-card--yellow bg-white p-5 rounded-xl shadow border-4 border-blue-800">
                  <div className="flex items-start justify-between">
                    <div className="flex flex-col gap-1">
                      <h3 className="text-xl font-bold text-blue-900">
                        <span className="bus-plate">{plate}</span>
                      </h3>
                      <div className="chips mt-1">
                        <span className="chip chip--meta">🚌 {l.type}</span>
                        <span className="chip chip--meta">⚙️ {l.km?.toLocaleString?.() || l.km} km</span>
                        <span className="chip chip--meta">🛠️ {l.year}</span>
                      </div>
                    </div>
                    <span className="badge-status is-idle">Your listing</span>
                  </div>

                  <div className="mt-2">
                    <span className={`badge-status ${issues.length ? "is-broken" : "is-ok"}`}>
                      {issues.length ? `Issues: ${issues.length}` : "No issues"}
                    </span>
                    {issues.length > 0 && (
                      <ul className="mt-2 list-disc ml-5 text-sm text-gray-800">
                        {issues.slice(0, 3).map((it, idx) => (
                          <li key={it.id || idx}>
                            {it.description}
                            {it.repair_time ? (
                              <span className="text-xs text-gray-600"> — repair: {String(it.repair_time)}</span>
                            ) : null}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>

                  <div className="mt-3 text-2xl font-extrabold text-blue-900">
                    <span className="price-tag">
                      <span className="coin" aria-hidden></span>
                      {Number(l.price).toLocaleString()} 💰
                    </span>
                  </div>
                  <div className="mt-4 flex gap-2">
                    <button
                      className="btn-industrial btn-industrial--danger text-black px-4 py-2 rounded"
                      onClick={() => {
                        openConfirm(
                          "Cancel listing",
                          "Cancel this listing?",
                          () => {
                            handleCancelListing(l.listing_id);
                            closeConfirm();
                          }
                        );
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="mb-12">
        <h2 className="section-title text-2xl font-semibold mb-4 text-center">Used Bus Listings</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {otherListings.map(l => {
            const plate = l.bus_plate;
            const hasIssuesData = Object.prototype.hasOwnProperty.call(issuesByPlate, plate);
            const issues = issuesByPlate[plate] || [];
            const selectedGarage = targetGarageByListing[l.listing_id];
            const canBuy = unlockedGarages.length > 0 && typeof selectedGarage === "number" && Number.isFinite(selectedGarage);
            return (
              <div key={l.listing_id} className="bus-card bus-card--idle bg-white p-5 rounded-xl shadow border-4 border-blue-800 h-full flex flex-col">
                <div className="flex items-start justify-between">
                  <div className="flex flex-col gap-1">
                    <h3 className="text-xl font-bold text-blue-900">
                      <span className="bus-plate">{plate}</span>
                    </h3>
                    <div className="chips mt-1">
                      <span className="chip chip--meta">🚌 {l.type}</span>
                      <span className="chip chip--meta">⚙️ {l.km?.toLocaleString?.() || l.km} km</span>
                      <span className="chip chip--meta">🛠️ {l.year}</span>
                    </div>
                  </div>
                  <span className="badge-status is-ok">Available</span>
                </div>

                {hasIssuesData && (
                  <div className="mt-2">
                    <span className={`badge-status ${issues.length ? "is-broken" : "is-ok"}`}>
                      {issues.length ? `Issues: ${issues.length}` : "No issues"}
                    </span>
                    {issues.length > 0 && (
                      <ul className="mt-2 list-disc ml-5 text-sm text-gray-800">
                        {issues.slice(0, 3).map((it, idx) => (
                          <li key={it.id || idx}>
                            {it.description}
                            {it.repair_time ? (
                              <span className="text-xs text-gray-600"> — repair: {String(it.repair_time)}</span>
                            ) : null}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                <div className="mt-3">
                  <label className="text-sm text-gray-700 mr-2">Store in garage:</label>
                  <select
                    className="input-industrial border p-2 rounded"
                    value={selectedGarage ?? ""}
                    onChange={e => {
                      const v = e.target.value;
                      setTargetGarageByListing(m => ({ ...m, [l.listing_id]: v === "" ? "" : Number(v) }));
                    }}
                  >
                    <option value="">{unlockedGarages.length ? "Select garage" : "No unlocked garages"}</option>
                    {unlockedGarages.map(g => (
                      <option key={g.id} value={g.id}>{g.name || `Garage #${g.id}`}</option>
                    ))}
                  </select>
                </div>

                <div className="mt-auto pt-3 flex items-center justify-between">
                  <div className="text-2xl font-extrabold text-blue-900">
                    <span className="price-tag">
                      <span className="coin" aria-hidden></span>
                      {Number(l.price).toLocaleString()} 💰
                    </span>
                  </div>
                  <button
                    className="btn-industrial btn-industrial--primary text-black px-5 py-2 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={!canBuy}
                    onClick={() => {
                      openConfirm(
                        "Confirm Purchase",
                        `Buy ${plate} for ${Number(l.price).toLocaleString()} 💰?`,
                        () => {
                          handleBuyListing(l.listing_id);
                          closeConfirm();
                        }
                      );
                    }}
                  >
                    Buy
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mb-10">
        <h2 className="section-title text-2xl font-semibold mb-4 text-center">Used Buses</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {buses.map((bus) => {
            const plate = bus.plate;
            const hasIssuesData = Object.prototype.hasOwnProperty.call(issuesByPlate, plate);
            const issues = issuesByPlate[plate] || [];
            const price = calculatePrice(bus.km);
            const selectedGarage = targetGarageByBus[plate];
            const canBuy = unlockedGarages.length > 0 && typeof selectedGarage === "number" && Number.isFinite(selectedGarage);
            return (
              <div key={bus.id || plate} className="bus-card bus-card--idle bg-white p-5 rounded-xl shadow border-2 border-blue-800 h-full flex flex-col">
                <div className="flex items-start justify-between">
                  <div className="flex flex-col gap-1">
                    <h2 className="text-xl font-bold text-blue-900">
                      <span className="bus-plate">{plate}</span>
                    </h2>
                    <div className="chips mt-1">
                      <span className="chip chip--meta">🚌 {bus.type}</span>
                      <span className="chip chip--meta">🛠️ {bus.year}</span>
                    </div>
                  </div>
                  <span className="badge-status is-ok">Available</span>
                </div>

                {hasIssuesData && (
                  <div className="mt-2">
                    <span className={`badge-status ${issues.length ? "is-broken" : "is-ok"}`}>
                      {issues.length ? `Issues: ${issues.length}` : "No issues"}
                    </span>
                    {issues.length > 0 && (
                      <ul className="mt-2 list-disc ml-5 text-sm text-gray-800">
                        {issues.slice(0, 3).map((it, idx) => (
                          <li key={it.id || idx}>
                            {it.description}
                            {it.repair_time ? (
                              <span className="text-xs text-gray-600"> — repair: {String(it.repair_time)}</span>
                            ) : null}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                <div className="mt-3">
                  <label className="text-sm text-gray-700 mr-2">Store in garage:</label>
                  <select
                    className="input-industrial border p-2 rounded"
                    value={selectedGarage ?? ""}
                    onChange={e => {
                      const v = e.target.value;
                      setTargetGarageByBus(m => ({ ...m, [plate]: v === "" ? "" : Number(v) }));
                    }}
                  >
                    <option value="">{unlockedGarages.length ? "Select garage" : "No unlocked garages"}</option>
                    {unlockedGarages.map(g => (
                      <option key={g.id} value={g.id}>{g.name || `Garage #${g.id}`}</option>
                    ))}
                  </select>
                </div>

                <div className="mt-auto pt-3 flex items-center justify-between">
                  <div className="text-2xl font-extrabold text-blue-900">
                    <span className="price-tag">
                      <span className="coin" aria-hidden></span>
                      {price.toLocaleString()} 💰
                    </span>
                  </div>
                  <button
                    onClick={() => {
                      openConfirm(
                        "Confirm Purchase",
                        `Buy ${plate} for ${price.toLocaleString()} 💰?`,
                        () => {
                          handleBuyUsed(plate, price);
                          closeConfirm();
                        }
                      );
                    }}
                    className="btn-industrial btn-industrial--primary text-black px-5 py-2 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={!canBuy}
                  >
                    Buy
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}