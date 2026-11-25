import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";

const TABS = [
  { id: "shop", label: "Shop" },
  { id: "cart", label: "Cart" },
  { id: "wishlist", label: "Wishlist" },
  { id: "orders", label: "My Orders" },
  { id: "admin", label: "Admin" },
];

export default function Navbar({ tab, setTab }) {
  const { customer, logout } = useAuth();
  const { count } = useCart();

  return (
    <header className="topbar">
      <div className="brand-block" onClick={() => setTab("shop")} role="button">
        <span className="brand-mark">ShopVault</span>
        <span className="brand-sub">Inventory-aware commerce</span>
      </div>

      {customer && (
        <nav className="nav-tabs">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`nav-tab ${tab === t.id ? "active" : ""}`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
              {t.id === "cart" && count > 0 && (
                <span className="cart-count">{count}</span>
              )}
            </button>
          ))}
        </nav>
      )}

      <div className="topbar-right">
        {customer ? (
          <>
            <span className="user-chip">{customer.full_name}</span>
            <button className="btn btn-ghost" onClick={logout}>
              Sign out
            </button>
          </>
        ) : (
          <span className="user-chip muted">Sign in to shop</span>
        )}
      </div>
    </header>
  );
}
