import { useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import StockBadge from "./StockBadge";

export default function ProductCatalog({ onOpenProduct, showToast }) {
  const { customer } = useAuth();
  const { addItem } = useCart();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [categoryId, setCategoryId] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [cats, prods] = await Promise.all([
        api.categories(),
        api.products({
          category_id: categoryId || undefined,
          search: search || undefined,
        }),
      ]);
      setCategories(cats);
      setProducts(prods);
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categoryId]);

  const handleSearch = (e) => {
    e.preventDefault();
    load();
  };

  const addToCart = (product) => {
    if (product.stock_quantity === 0) return;
    addItem(product, 1);
    showToast(`Added ${product.name} to cart`, "success");
  };

  const addWishlist = async (product) => {
    try {
      await api.addWishlist({
        customer_id: customer.customer_id,
        product_id: product.product_id,
      });
      showToast("Saved to wishlist", "success");
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>Catalog</h2>
          <p>Live stock badges update from the Inventory table.</p>
        </div>
        <form className="filters" onSubmit={handleSearch}>
          <select
            value={categoryId}
            onChange={(e) => setCategoryId(e.target.value)}
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c.category_id} value={c.category_id}>
                {c.category_name}
              </option>
            ))}
          </select>
          <input
            placeholder="Search products…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button className="btn btn-secondary" type="submit">
            Search
          </button>
        </form>
      </div>

      {loading ? (
        <p className="muted">Loading products…</p>
      ) : (
        <div className="product-grid">
          {products.map((p) => (
            <article key={p.product_id} className="product-tile">
              <button
                className="product-title-btn"
                onClick={() => onOpenProduct(p.product_id)}
              >
                <h3>{p.name}</h3>
              </button>
              <p className="meta">
                {p.category_name}
                {p.average_rating != null && (
                  <> · ★ {p.average_rating} ({p.review_count})</>
                )}
              </p>
              <p className="price">₹{Number(p.price).toLocaleString()}</p>
              <StockBadge status={p.stock_status} badge={p.stock_badge} />
              <p className="desc">{p.description}</p>
              <div className="tile-actions">
                {p.stock_quantity === 0 ? (
                  <button className="btn btn-disabled" disabled>
                    Out of Stock
                  </button>
                ) : (
                  <button
                    className="btn btn-primary"
                    onClick={() => addToCart(p)}
                  >
                    Add to cart
                  </button>
                )}
                <button
                  className="btn btn-ghost"
                  onClick={() => addWishlist(p)}
                >
                  Wishlist
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
