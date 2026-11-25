import { useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import StockBadge from "./StockBadge";

export default function ProductDetail({ productId, onBack, showToast }) {
  const { customer } = useAuth();
  const { addItem } = useCart();
  const [product, setProduct] = useState(null);
  const [summary, setSummary] = useState(null);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");

  const load = async () => {
    try {
      const [p, reviews] = await Promise.all([
        api.product(productId),
        api.productReviews(productId),
      ]);
      setProduct(p);
      setSummary(reviews);
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productId]);

  const submitReview = async (e) => {
    e.preventDefault();
    try {
      await api.createReview({
        customer_id: customer.customer_id,
        product_id: productId,
        rating: Number(rating),
        comment,
      });
      setComment("");
      showToast("Review submitted", "success");
      load();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  if (!product) return <p className="muted">Loading…</p>;

  return (
    <section className="section">
      <button className="btn btn-ghost" onClick={onBack}>
        ← Back to catalog
      </button>
      <div className="detail-layout">
        <div>
          <h2>{product.name}</h2>
          <p className="meta">{product.category_name}</p>
          <p className="price large">₹{Number(product.price).toLocaleString()}</p>
          <StockBadge status={product.stock_status} badge={product.stock_badge} />
          <p className="desc spaced">{product.description}</p>
          <div className="tile-actions">
            {product.stock_quantity === 0 ? (
              <button className="btn btn-disabled" disabled>
                Out of Stock
              </button>
            ) : (
              <button
                className="btn btn-primary"
                onClick={() => {
                  addItem(product, 1);
                  showToast("Added to cart", "success");
                }}
              >
                Add to cart
              </button>
            )}
          </div>
        </div>

        <div className="reviews-panel">
          <h3>
            Reviews
            {summary?.average_rating != null && (
              <span className="avg-pill">
                AVG({summary.average_rating}) · {summary.review_count} reviews
              </span>
            )}
          </h3>
          <ul className="review-list">
            {(summary?.reviews || []).map((r) => (
              <li key={r.review_id}>
                <strong>{r.customer_name}</strong>
                <span> ★ {r.rating}</span>
                <p>{r.comment}</p>
              </li>
            ))}
            {summary?.review_count === 0 && (
              <li className="muted">No reviews yet.</li>
            )}
          </ul>

          <form className="review-form" onSubmit={submitReview}>
            <label>
              Rating
              <select value={rating} onChange={(e) => setRating(e.target.value)}>
                {[5, 4, 3, 2, 1].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Comment
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={3}
              />
            </label>
            <button className="btn btn-secondary" type="submit">
              Post review
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}
