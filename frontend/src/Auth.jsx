import { useState } from "react";
import axios from "axios";

export default function Auth({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLogin, setIsLogin] = useState(true);
  const [message, setMessage] = useState("");
  const [showPwd, setShowPwd] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const url = isLogin ? "http://localhost:5000/login" : "http://localhost:5000/register";
    try {
      const res = await axios.post(url, { username, password }, { withCredentials: true });
      setMessage(res.data.message);
      if (isLogin) onLogin();
    } catch (err) {
      setMessage(err.response?.data?.error || "Error");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white from-slate-50 to-slate-200 p-6">
      <form
        onSubmit={handleSubmit}
        autoComplete="off"
        className="panel bg-white p-8 rounded-2xl shadow-lg border-4 border-blue-800 w-full max-w-sm"
      >
        <div className="text-center mb-6">
          <div className="text-4xl mb-2" aria-hidden>🚌</div>
          <h2 className="section-title text-3xl font-bold mb-1">{isLogin ? "Welcome back" : "Create account"}</h2>
          <p className="text-gray-600">{isLogin ? "Sign in to continue" : "Register to get started"}</p>
        </div>

        <input
          type="password"
          name="dummy_password"
          autoComplete="new-password"
          tabIndex={-1}
          aria-hidden="true"
          style={{ position: "absolute", left: "-9999px", width: 0, height: 0, opacity: 0 }}
        />

        <label className="bus-meta-label text-xs text-gray-600 font-semibold">USERNAME</label>
        <input
          className="w-full p-2 mb-4 input-industrial border rounded"
          placeholder="Your username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          name="username"
          autoComplete="off"
          autoCorrect="off"
          autoCapitalize="none"
          spellCheck={false}
        />

        <label className="bus-meta-label text-xs text-gray-600 font-semibold">PASSWORD</label>
        <div className="relative mb-4">
          <input
            type={showPwd ? "text" : "password"}
            className="w-full p-2 input-industrial border rounded pr-20"
            placeholder="Your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            name="password"
            autoComplete={isLogin ? "current-password" : "new-password"}
          />
        </div>

        <button type="submit" className="w-full btn-industrial btn-industrial--primary py-3 rounded font-bold mb-3">
          {isLogin ? "Login" : "Register"}
        </button>

        <button
          type="button"
          className="w-full btn-industrial btn-industrial--secondary py-2 rounded"
          onClick={() => setIsLogin(!isLogin)}
        >
          {isLogin ? "Switch to Register" : "Switch to Login"}
        </button>

        {message && (
          <p className={`mt-4 text-center font-semibold ${/error|fail|invalid/i.test(message) ? "text-red-700" : "text-green-700"}`}>
            {message}
          </p>
        )}
      </form>
    </div>
  );
}
