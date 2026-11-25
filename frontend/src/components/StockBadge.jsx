export default function StockBadge({ status, badge }) {
  const isHealthy = status === "in_stock";
  const cls = isHealthy ? "badge badge-green" : "badge badge-red";
  return <span className={cls}>{badge}</span>;
}
