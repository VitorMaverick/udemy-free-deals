import { Link, useLocation } from "react-router-dom";

const links = [
  { to: "/admin/dashboard", label: "📊 Dashboard" },
  { to: "/admin/crawler-results", label: "🔍 Detectados" },
  { to: "/admin/ready-to-publish", label: "✅ Publicar" },
  { to: "/admin/logs", label: "📋 Logs" },
];

export default function AdminNav() {
  const { pathname } = useLocation();

  return (
    <nav className="flex gap-2 mb-6 flex-wrap border-b pb-3">
      {links.map((l) => (
        <Link
          key={l.to}
          to={l.to}
          className={`px-3 py-1.5 rounded text-sm ${
            pathname === l.to
              ? "bg-purple-600 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          {l.label}
        </Link>
      ))}
    </nav>
  );
}
