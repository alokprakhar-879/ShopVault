import { useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";

export default function WishlistView({ showToast, onOpenProduct }) {
  const { customer } = useAuth();
  const { addItem } = useCart();
  const [items, setItems] = useState([]);

  const load = async () => {
    try {
      const data = await api.wishlist(customer.customer_id);
      setItems(data);
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customer.customer_id]);

  const remove = async (id) => {
    try {
      await api.removeWishlist(id);
      showToast("Removed from wishlist", "success");
      load();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>Wishlist</h2>
          <p>Saved for later — backed by the Wishlists table.</p>
        </div>
      </div>
      {!items.length ? (
        <p className="muted">No saved items yet.</p>
      ) : (
        <ul className="simple-list">
          {items.map((w) => (
            <li key={w.wishlist_id}>
              <div>
                <button
                  className="linkish"
                  onClick={() => onOpenProduct(w.product_id)}
                >
                  {w.product_name}
                </button>
                <p className="meta">
                  ₹{Number(w.price).toLocaleString()} · {w.stock_badge}
                </p>
              </div>
              <div className="tile-actions">
                {w.stock_quantity > 0 && (
                  <button
                    className="btn btn-secondary"
                    onClick={() => {
                      addItem(
                        {
                          product_id: w.product_id,
                          name: w.product_name,
                          price: w.price,
                          stock_quantity: w.stock_quantity,
                        },
                        1
                      );
                      showToast("Moved to cart", "success");
                    }}
                  >
                    Add to cart
                  </button>
                )}
                <button
                  className="btn btn-ghost"
                  onClick={() => remove(w.wishlist_id)}
                >
                  Remove
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
