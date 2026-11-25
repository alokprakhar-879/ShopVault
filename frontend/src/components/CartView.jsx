import { useState } from "react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";

export default function CartView({ showToast, setTab }) {
  const { customer } = useAuth();
  const { items, updateQty, removeItem, replaceCart, clearCart, total } =
    useCart();
  const [method, setMethod] = useState("UPI");
  const [simulateFail, setSimulateFail] = useState(false);
  const [busy, setBusy] = useState(false);

  const checkout = async () => {
    if (!items.length) return;
    setBusy(true);
    try {
      const payloadItems = items.map((i) => ({
        product_id: i.product_id,
        quantity: i.quantity,
      }));

      // Pre-checkout validation (Edge Case 1)
      const validation = await api.validateCart(payloadItems);
      if (!validation.valid) {
        const refreshed = (validation.refreshed_items || []).map((ri) => {
          const prev = items.find((i) => i.product_id === ri.product_id);
          return {
            product_id: ri.product_id,
            name: prev?.name || `Product #${ri.product_id}`,
            price: prev?.price || 0,
            quantity: ri.quantity,
          };
        });
        replaceCart(refreshed);
        showToast(
          validation.message ||
            "Sorry! Someone else just bought these items. We've updated your cart",
          "error"
        );
        setBusy(false);
        return;
      }

      const result = await api.checkout({
        customer_id: customer.customer_id,
        items: payloadItems,
        payment_method: method,
        simulate_payment_failure: simulateFail,
      });

      if (!result.success) {
        if (result.cart_issues?.length) {
          const refreshed = result.cart_issues
            .filter((i) => i.available > 0)
            .map((i) => {
              const prev = items.find((x) => x.product_id === i.product_id);
              return {
                product_id: i.product_id,
                name: i.product_name,
                price: prev?.price || 0,
                quantity: i.available,
              };
            });
          // Keep items that had no issues
          const issueIds = new Set(result.cart_issues.map((i) => i.product_id));
          const ok = items
            .filter((i) => !issueIds.has(i.product_id))
            .concat(refreshed);
          replaceCart(ok);
        }
        showToast(result.message, "error");
        // If payment failed, the order and failed payment record were saved in the DB
        if (result.order) {
          clearCart();
          setTab("orders");
        }
        return;
      }

      clearCart();
      showToast(result.message, "success");
      setTab("orders");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>Your cart</h2>
          <p>
            Checkout uses <code>SELECT … FOR UPDATE</code> and records failed
            payments safely without deducting stock.
          </p>
        </div>
      </div>

      {!items.length ? (
        <p className="muted">Cart is empty.</p>
      ) : (
        <div className="cart-layout">
          <ul className="cart-list">
            {items.map((item) => (
              <li key={item.product_id}>
                <div>
                  <strong>{item.name}</strong>
                  <p className="meta">
                    ₹{Number(item.price).toLocaleString()} each
                  </p>
                </div>
                <div className="qty-controls">
                  <button
                    onClick={() => updateQty(item.product_id, item.quantity - 1)}
                  >
                    −
                  </button>
                  <span>{item.quantity}</span>
                  <button
                    onClick={() => updateQty(item.product_id, item.quantity + 1)}
                  >
                    +
                  </button>
                  <button
                    className="btn btn-ghost"
                    onClick={() => removeItem(item.product_id)}
                  >
                    Remove
                  </button>
                </div>
              </li>
            ))}
          </ul>

          <aside className="checkout-panel">
            <p className="total">
              Total <strong>₹{total.toLocaleString()}</strong>
            </p>
            <label>
              Payment method
              <select value={method} onChange={(e) => setMethod(e.target.value)}>
                <option>UPI</option>
                <option>Credit Card</option>
                <option>PayPal</option>
              </select>
            </label>
            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={simulateFail}
                onChange={(e) => setSimulateFail(e.target.checked)}
              />
              Simulate payment failure (preserve failed audit demo)
            </label>
            <button
              className="btn btn-primary"
              onClick={checkout}
              disabled={busy}
            >
              {busy ? "Processing…" : "Checkout securely"}
            </button>
          </aside>
        </div>
      )}
    </section>
  );
}
