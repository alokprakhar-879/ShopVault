const BASE = import.meta.env.VITE_API_URL || "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = data.detail || data.message || res.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

export const api = {
  health: () => request("/health"),
  categories: () => request("/categories"),
  products: (params = {}) => {
    const q = new URLSearchParams();
    if (params.category_id) q.set("category_id", params.category_id);
    if (params.search) q.set("search", params.search);
    const qs = q.toString();
    return request(`/products${qs ? `?${qs}` : ""}`);
  },
  product: (id) => request(`/products/${id}`),
  customers: () => request("/customers"),
  login: (email) =>
    request(`/customers/login?email=${encodeURIComponent(email)}`, {
      method: "POST",
    }),
  createCustomer: (body) =>
    request("/customers", { method: "POST", body: JSON.stringify(body) }),
  validateCart: (items) =>
    request("/orders/validate-cart", {
      method: "POST",
      body: JSON.stringify({ items }),
    }),
  checkout: (body) =>
    request("/orders/checkout", { method: "POST", body: JSON.stringify(body) }),
  orders: (customerId) => request(`/orders?customer_id=${customerId}`),
  cancelOrder: (orderId) =>
    request(`/orders/${orderId}/cancel`, { method: "POST" }),
  updateOrderStatus: (orderId, status) =>
    request(`/orders/${orderId}/status?status=${encodeURIComponent(status)}`, {
      method: "PATCH",
    }),
  wishlist: (customerId) => request(`/wishlists?customer_id=${customerId}`),
  addWishlist: (body) =>
    request("/wishlists", { method: "POST", body: JSON.stringify(body) }),
  removeWishlist: (id) => request(`/wishlists/${id}`, { method: "DELETE" }),
  productReviews: (productId) => request(`/reviews/product/${productId}`),
  createReview: (body) =>
    request("/reviews", { method: "POST", body: JSON.stringify(body) }),
  adminLogin: (body) =>
    request("/admin/login", { method: "POST", body: JSON.stringify(body) }),
  adminDashboard: (accessKey) =>
    request("/admin/dashboard", {
      headers: { "x-admin-key": accessKey },
    }),
  lowStock: () => request("/inventory/low-stock"),
  updateInventory: (productId, body) =>
    request(`/inventory/${productId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
};
