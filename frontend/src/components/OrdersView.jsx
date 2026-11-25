import { useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

export default function OrdersView({ showToast }) {
  const { customer } = useAuth();
  const [orders, setOrders] = useState([]);

  const load = async () => {
    try {
      const data = await api.orders(customer.customer_id);
      setOrders(data);
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customer.customer_id]);

  const cancel = async (order) => {
    try {
      const result = await api.cancelOrder(order.order_id);
      showToast(result.message, result.success ? "success" : "error");
      load();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>My Orders</h2>
          <p>
            Live status tracking — Pending 🟡 · Shipped 🔵 · Delivered 🟢 ·
            Cancelled 🔴
          </p>
        </div>
        <button className="btn btn-ghost" onClick={load}>
          Refresh
        </button>
      </div>

      {!orders.length ? (
        <p className="muted">No orders yet.</p>
      ) : (
        <div className="orders-stack">
          {orders.map((o) => {
            const isPaymentFailed = o.payment?.payment_status === "Failed";
            return (
              <article key={o.order_id} className="order-card">
                <div className="order-head">
                  <h3>
                    Order #{o.order_id}{" "}
                    <span className="status-pill">
                      {o.status_emoji} {o.order_status}
                    </span>
                    {isPaymentFailed && (
                      <span
                        className="badge badge-red"
                        style={{ marginLeft: "0.5rem" }}
                      >
                        Payment Failed
                      </span>
                    )}
                  </h3>
                  <p className="meta">
                    {new Date(o.order_date).toLocaleString()} · ₹
                    {Number(o.total_amount).toLocaleString()}
                    {o.payment && (
                      <>
                        {" · "}Payment{" "}
                        <span
                          style={{
                            color:
                              o.payment.payment_status === "Success"
                                ? "#2e7d32"
                                : isPaymentFailed
                                ? "#d32f2f"
                                : "#e65100",
                            fontWeight: 600,
                          }}
                        >
                          {o.payment.payment_status}
                        </span>{" "}
                        ({o.payment.payment_method})
                      </>
                    )}
                  </p>
                </div>
                <ul>
                  {o.items.map((item) => (
                    <li key={item.order_item_id}>
                      {item.product_name} × {item.quantity} @ ₹
                      {Number(item.unit_price).toLocaleString()}
                    </li>
                  ))}
                </ul>
                {o.can_cancel ? (
                  <button
                    className="btn btn-secondary"
                    onClick={() => cancel(o)}
                  >
                    Cancel & restock
                  </button>
                ) : isPaymentFailed ? (
                  <p className="muted" style={{ color: "#d32f2f" }}>
                    Payment failed — order cancelled with 0 stock deducted.
                  </p>
                ) : o.order_status === "Cancelled" ? (
                  <p className="muted">Order cancelled — stock restored.</p>
                ) : (
                  <button
                    className="btn btn-disabled"
                    disabled
                    title="This order has already shipped. Please request a return instead"
                  >
                    Cancel unavailable
                  </button>
                )}
                {!o.can_cancel &&
                  !isPaymentFailed &&
                  (o.order_status === "Shipped" ||
                    o.order_status === "Delivered") && (
                    <p className="hint warn">
                      This order has already shipped. Please request a return
                      instead.
                    </p>
                  )}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
