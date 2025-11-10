import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import axios from "axios";

export default function Navbar({ balance, onLogout }) {
  const { pathname } = useLocation();
  const [open, setOpen] = useState(false);
  const [username, setUsername] = useState("");

  useEffect(() => {
    axios
      .get("http://localhost:5000/session", { withCredentials: true })
      .then((res) => setUsername(res.data?.username || ""))
      .catch(() => setUsername(""));
  }, []);

  const items = [
    { to: "/", label: "Home" },
    { to: "/market", label: "Market" },
    { to: "/issues", label: "Issues" },
    { to: "/garages", label: "Garages" },
    { to: "/lines", label: "Lines" },
    { to: "/schedules", label: "Schedules" },
  ];

  const linkCls = (to) =>
    `px-3 py-1 rounded btn-industrial ${
      pathname === to
        ? "btn-industrial--primary font-extrabold ring-2 ring-blue-600"
        : "btn-industrial--secondary hover:bg-blue-100"
    } transition`;

  return (
    <nav className="sticky top-0 z-40 bg-white/90 backdrop-blur border-b-4 border-blue-800 shadow">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            className="md:hidden btn-industrial btn-industrial--secondary px-3 py-1 rounded"
            onClick={() => setOpen((o) => !o)}
            aria-label="Toggle menu"
          >
            ☰
          </button>
          <Link to="/" className="text-xl font-extrabold text-blue-900 flex items-center gap-2">
            <span aria-hidden>🌀</span>
            {username ? username : "User"}
          </Link>
          <div className="hidden md:flex items-center gap-2 ml-4">
            {items.map((it) => (
              <Link key={it.to} to={it.to} className={linkCls(it.to)}>
                {it.label}
              </Link>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {balance !== null && (
            <span className="btn-industrial btn-industrial--secondary px-4 py-1.5 rounded-lg text-xl font-extrabold tracking-wide">
              💰 {Number(balance).toLocaleString?.() || balance}
            </span>
          )}
          <button onClick={onLogout} className="btn-industrial btn-industrial--danger px-3 py-1 rounded">
            Logout
          </button>
        </div>
      </div>

      {open && (
        <div className="md:hidden border-t border-blue-200 bg-white/95">
          <div className="max-w-6xl mx-auto px-4 py-3 flex flex-col gap-2">
            {items.map((it) => (
              <Link
                key={it.to}
                to={it.to}
                className={linkCls(it.to)}
                onClick={() => setOpen(false)}
              >
                {it.label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}
