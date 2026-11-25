import { useState } from "react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

export default function LoginPanel({ onSuccess }) {
  const { login } = useAuth();
  const [email, setEmail] = useState("aisha@example.com");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    phone: "",
    address: "",
  });

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const user = await api.login(email.trim());
      login(user);
      onSuccess?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const user = await api.createCustomer(form);
      login(user);
      onSuccess?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="hero-login">
      <div className="hero-copy">
        <p className="eyebrow">DBMS Project MVP</p>
        <h1 className="hero-brand">ShopVault</h1>
        <p className="hero-lead">
          Browse live inventory, save wishlists, checkout with row-level locks,
          and track orders — backed by PostgreSQL and FastAPI.
        </p>
      </div>

      <div className="auth-panel">
        <div className="auth-toggle">
          <button
            className={mode === "login" ? "active" : ""}
            onClick={() => setMode("login")}
            type="button"
          >
            Sign in
          </button>
          <button
            className={mode === "register" ? "active" : ""}
            onClick={() => setMode("register")}
            type="button"
          >
            Register
          </button>
        </div>

        {mode === "login" ? (
          <form onSubmit={handleLogin} className="auth-form">
            <label>
              Email
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </label>
            <p className="hint">
              Try <code>aisha@example.com</code> or <code>rohan@example.com</code>
            </p>
            {error && <p className="form-error">{error}</p>}
            <button className="btn btn-primary" disabled={loading}>
              {loading ? "Signing in…" : "Enter store"}
            </button>
          </form>
        ) : (
          <form onSubmit={handleRegister} className="auth-form">
            {["full_name", "email", "phone", "address"].map((field) => (
              <label key={field}>
                {field.replace("_", " ")}
                <input
                  type={field === "email" ? "email" : "text"}
                  value={form[field]}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, [field]: e.target.value }))
                  }
                  required={field === "full_name" || field === "email"}
                />
              </label>
            ))}
            {error && <p className="form-error">{error}</p>}
            <button className="btn btn-primary" disabled={loading}>
              {loading ? "Creating…" : "Create account"}
            </button>
          </form>
        )}
      </div>
    </section>
  );
}
