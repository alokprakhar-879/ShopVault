import { useState } from "react";
import Navbar from "./components/Navbar";
import LoginPanel from "./components/LoginPanel";
import ProductCatalog from "./components/ProductCatalog";
import CartView from "./components/CartView";
import WishlistView from "./components/WishlistView";
import OrdersView from "./components/OrdersView";
import ProductDetail from "./components/ProductDetail";
import AdminDashboard from "./components/AdminDashboard";
import Toast from "./components/Toast";
import { useAuth } from "./context/AuthContext";

export default function App() {
  const { customer } = useAuth();
  const [tab, setTab] = useState("shop");
  const [toast, setToast] = useState(null);
  const [selectedProductId, setSelectedProductId] = useState(null);

  const showToast = (message, type = "info") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4500);
  };

  const openProduct = (id) => {
    setSelectedProductId(id);
    setTab("detail");
  };

  return (
    <div className="app-shell">
      <div className="bg-atmosphere" aria-hidden="true" />
      <Navbar tab={tab} setTab={setTab} />
      {toast && <Toast message={toast.message} type={toast.type} />}

      <main className="main-stage">
        {!customer ? (
          <LoginPanel onSuccess={() => showToast("Welcome back!", "success")} />
        ) : (
          <>
            {tab === "shop" && (
              <ProductCatalog
                onOpenProduct={openProduct}
                showToast={showToast}
              />
            )}
            {tab === "detail" && selectedProductId && (
              <ProductDetail
                productId={selectedProductId}
                onBack={() => setTab("shop")}
                showToast={showToast}
              />
            )}
            {tab === "cart" && <CartView showToast={showToast} setTab={setTab} />}
            {tab === "wishlist" && (
              <WishlistView showToast={showToast} onOpenProduct={openProduct} />
            )}
            {tab === "orders" && <OrdersView showToast={showToast} />}
            {tab === "admin" && <AdminDashboard showToast={showToast} />}
          </>
        )}
      </main>
    </div>
  );
}
