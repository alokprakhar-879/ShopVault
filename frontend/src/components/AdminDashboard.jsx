import { useEffect, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line, Bar } from "react-chartjs-2";
import { api } from "../api";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const ADMIN_KEY_STORAGE = "shopvault_admin_key";

export default function AdminDashboard({ showToast }) {
  /* ---- admin auth gate state ---- */
  const [accessKey, setAccessKey] = useState(
    () => sessionStorage.getItem(ADMIN_KEY_STORAGE) || ""
  );
  const [authenticated, setAuthenticated] = useState(!!accessKey);
  const [loginForm, setLoginForm] = useState({
    email: "",
    password: "",
    access_key: "",
  });
  const [loginError, setLoginError] = useState("");

  /* ---- dashboard state ---- */
  const [data, setData] = useState(null);
  const [restockQty, setRestockQty] = useState({});

  /* ---- admin login ---- */
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError("");
    try {
      const res = await api.adminLogin(loginForm);
      if (res.success) {
        setAccessKey(res.access_key);
        sessionStorage.setItem(ADMIN_KEY_STORAGE, res.access_key);
        setAuthenticated(true);
      }
    } catch (err) {
      setLoginError(err.message || "Invalid admin credentials");
    }
  };

  const handleLogout = () => {
    setAccessKey("");
    setAuthenticated(false);
    sessionStorage.removeItem(ADMIN_KEY_STORAGE);
    setData(null);
  };

  /* ---- dashboard data ---- */
  const load = async () => {
    try {
      const dash = await api.adminDashboard(accessKey);
      setData(dash);
    } catch (err) {
      if (err.message?.includes("403") || err.message?.includes("admin")) {
        handleLogout();
        showToast("Admin session expired — please sign in again", "error");
      } else {
        showToast(err.message, "error");
      }
    }
  };

  useEffect(() => {
    if (authenticated && accessKey) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authenticated]);

  /* ---- restock handler ---- */
  const restock = async (productId) => {
    const qty = Number(restockQty[productId] || 10);
    try {
      const item = data.all_inventory.find((i) => i.product_id === productId);
      await api.updateInventory(productId, {
        stock_quantity: (item?.stock_quantity || 0) + qty,
      });
      showToast("Inventory updated", "success");
      load();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  const shipPending = async () => {
    try {
      const customers = await api.customers();
      for (const c of customers) {
        const orders = await api.orders(c.customer_id);
        for (const o of orders) {
          if (o.order_status === "Pending") {
            await api.updateOrderStatus(o.order_id, "Shipped");
          }
        }
      }
      showToast("Pending orders marked Shipped (demo)", "success");
      load();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  /* ==================== LOGIN GATE ==================== */
  if (!authenticated) {
    return (
      <section className="section">
        <div className="admin-login-gate">
          <h2>🔒 Admin Sign-In</h2>
          <p className="meta">
            Enter admin credentials to access the dashboard.
          </p>
          <form className="admin-login-form" onSubmit={handleLogin}>
            <label>
              Email
              <input
                type="email"
                value={loginForm.email}
                onChange={(e) =>
                  setLoginForm((f) => ({ ...f, email: e.target.value }))
                }
                required
                autoFocus
              />
            </label>
            <label>
              Password
              <input
                type="password"
                value={loginForm.password}
                onChange={(e) =>
                  setLoginForm((f) => ({ ...f, password: e.target.value }))
                }
                required
              />
            </label>
            <label>
              Access Key
              <input
                type="password"
                value={loginForm.access_key}
                onChange={(e) =>
                  setLoginForm((f) => ({ ...f, access_key: e.target.value }))
                }
                required
              />
            </label>
            {loginError && <p className="danger">{loginError}</p>}
            <button className="btn btn-primary" type="submit">
              Sign in to Admin
            </button>
          </form>
        </div>
      </section>
    );
  }

  /* ==================== DASHBOARD ==================== */
  if (!data) return <p className="muted">Loading dashboard…</p>;

  const threshold = data.low_stock_threshold;

  const labels = data.sales_trend.map((p) => p.date.slice(5));
  const revenueData = {
    labels,
    datasets: [
      {
        label: "Daily revenue (₹)",
        data: data.sales_trend.map((p) => p.revenue),
        borderColor: "#0f6b5c",
        backgroundColor: "rgba(15, 107, 92, 0.15)",
        fill: true,
        tension: 0.35,
      },
    ],
  };
  const ordersData = {
    labels,
    datasets: [
      {
        label: "Orders / day",
        data: data.sales_trend.map((p) => p.order_count),
        backgroundColor: "#c45c26",
      },
    ],
  };

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>Admin dashboard</h2>
          <p>Sales trends via Chart.js · full inventory monitoring · payment audit</p>
        </div>
        <div className="tile-actions">
          <button className="btn btn-ghost" onClick={load}>
            Refresh
          </button>
          <button className="btn btn-secondary" onClick={shipPending}>
            Ship all pending (demo)
          </button>
          <button className="btn btn-danger" onClick={handleLogout}>
            🔓 Logout
          </button>
        </div>
      </div>

      <div className="kpi-row" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
        <div className="kpi">
          <span>Total revenue</span>
          <strong>₹{data.total_revenue.toLocaleString()}</strong>
        </div>
        <div className="kpi">
          <span>Total orders</span>
          <strong>{data.total_orders}</strong>
        </div>
        <div className="kpi">
          <span>Pending</span>
          <strong>{data.pending_orders}</strong>
        </div>
        <div className="kpi warn">
          <span>Low stock SKUs (≤ {threshold})</span>
          <strong>{data.low_stock_count}</strong>
        </div>
        <div className="kpi warn" style={{ borderColor: "rgba(211, 47, 47, 0.35)" }}>
          <span>Failed payments</span>
          <strong style={{ color: data.failed_payments_count > 0 ? "#d32f2f" : "inherit" }}>
            {data.failed_payments_count || 0}
          </strong>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-panel">
          <h3>Revenue trend (14 days)</h3>
          <Line
            data={revenueData}
            options={{
              responsive: true,
              plugins: { legend: { display: false } },
              scales: { y: { beginAtZero: true } },
            }}
          />
        </div>
        <div className="chart-panel">
          <h3>Order volume</h3>
          <Bar
            data={ordersData}
            options={{
              responsive: true,
              plugins: { legend: { display: false } },
              scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
            }}
          />
        </div>
      </div>

      {/* Failed Payments Audit Log */}
      {data.failed_payments && data.failed_payments.length > 0 && (
        <div className="low-stock-panel" style={{ marginTop: "1rem" }}>
          <h3>⚠️ Failed Payments Audit Log</h3>
          <p className="meta">
            Preserved in <code>payments</code> table (status: <code>Failed</code>) · Stock protected (0 deducted)
          </p>
          <table className="data-table">
            <thead>
              <tr>
                <th>Payment ID</th>
                <th>Order ID</th>
                <th>Customer</th>
                <th>Amount</th>
                <th>Method</th>
                <th>Date</th>
                <th>Status</th>
                <th>Stock Impact</th>
              </tr>
            </thead>
            <tbody>
              {data.failed_payments.map((p) => (
                <tr key={p.payment_id}>
                  <td>#{p.payment_id}</td>
                  <td>#{p.order_id}</td>
                  <td>
                    {p.customer_name}{" "}
                    <span className="meta">({p.customer_email})</span>
                  </td>
                  <td style={{ fontWeight: 600 }}>
                    ₹{Number(p.amount).toLocaleString()}
                  </td>
                  <td>{p.payment_method}</td>
                  <td>{new Date(p.transaction_date).toLocaleString()}</td>
                  <td>
                    <span className="badge badge-red">Failed</span>
                  </td>
                  <td style={{ color: "#2e7d32", fontWeight: 600 }}>
                    0 deducted (Safe)
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Full Inventory Monitoring Panel */}
      <div className="low-stock-panel">
        <h3>Inventory monitoring — All products</h3>
        <p className="meta">
          Dynamic stock status: <code>stock ≤ {threshold}</code> →{" "}
          <span style={{ color: "#d32f2f", fontWeight: 600 }}>Low Stock (RED)</span>
          {" · "}
          <code>stock &gt; {threshold}</code> →{" "}
          <span style={{ color: "#2e7d32", fontWeight: 600 }}>In Stock (GREEN)</span>
        </p>
        {!data.all_inventory.length ? (
          <p className="muted">No inventory rows found.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Stock</th>
                <th>Status</th>
                <th>Restock</th>
              </tr>
            </thead>
            <tbody>
              {data.all_inventory.map((item) => {
                const isLow = item.stock_quantity <= threshold;
                return (
                  <tr key={item.inventory_id}>
                    <td>{item.product_name}</td>
                    <td
                      style={{
                        color: isLow ? "#d32f2f" : "#2e7d32",
                        fontWeight: 600,
                      }}
                    >
                      {item.stock_quantity}
                    </td>
                    <td>
                      <span
                        className={
                          isLow ? "badge badge-red" : "badge badge-green"
                        }
                      >
                        {isLow
                          ? item.stock_quantity === 0
                            ? "Out of Stock"
                            : "Low Stock"
                          : "In Stock"}
                      </span>
                    </td>
                    <td className="restock-cell">
                      <input
                        type="number"
                        min="1"
                        value={restockQty[item.product_id] ?? 10}
                        onChange={(e) =>
                          setRestockQty((s) => ({
                            ...s,
                            [item.product_id]: e.target.value,
                          }))
                        }
                      />
                      <button
                        className="btn btn-secondary"
                        onClick={() => restock(item.product_id)}
                      >
                        Add stock
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}
