import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "../lib/api";
import AdminNav from "../components/AdminNav";

export default function AdminDashboard() {
  const [token, setToken] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const t = localStorage.getItem("admin_token");
    if (!t) { navigate("/admin"); return; }
    setToken(t);
  }, [navigate]);

  const { data: stats } = useQuery({
    queryKey: ["admin-stats", token],
    queryFn: () => api.getDashboard(token),
    enabled: !!token,
  });

  const crawlerMutation = useMutation({
    mutationFn: () => api.runCrawler(token),
  });

  const logout = () => { localStorage.removeItem("admin_token"); navigate("/admin"); };

  if (!token) return null;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-xl font-bold">Admin Dashboard</h1>
        <button onClick={logout} className="text-sm text-red-500 hover:underline">Logout</button>
      </div>
      <AdminNav />

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: "Pendentes", value: stats.pending_courses, color: "text-orange-600" },
            { label: "Com Link", value: stats.ready_courses, color: "text-blue-600" },
            { label: "Publicados", value: stats.published_courses, color: "text-green-600" },
            { label: "Clicks Hoje", value: stats.clicks_today, color: "text-purple-600" },
          ].map((s) => (
            <div key={s.label} className="bg-white p-4 rounded shadow text-center">
              <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
              <p className="text-xs text-gray-500">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="mb-8 flex flex-wrap gap-3">
        <button
          onClick={() => crawlerMutation.mutate()}
          disabled={crawlerMutation.isPending}
          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
        >
          {crawlerMutation.isPending ? "Iniciando..." : "🔄 Rodar Crawler"}
        </button>
        {crawlerMutation.isSuccess && (
          <span className="text-sm text-green-600 self-center">✅ Crawler iniciado em background</span>
        )}
      </div>

      {/* Navigation */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link to="/admin/crawler-results" className="bg-white p-5 rounded shadow hover:shadow-md transition-shadow border-l-4 border-orange-500">
          <h2 className="font-bold mb-1">🔍 Cursos Detectados</h2>
          <p className="text-sm text-gray-500">Ver cursos encontrados pelo crawler e cadastrar links de afiliado</p>
        </Link>
        <Link to="/admin/ready-to-publish" className="bg-white p-5 rounded shadow hover:shadow-md transition-shadow border-l-4 border-blue-500">
          <h2 className="font-bold mb-1">✅ Prontos para Publicar</h2>
          <p className="text-sm text-gray-500">Cursos com link cadastrado, prontos para o post do dia</p>
        </Link>
        <Link to="/admin/logs" className="bg-white p-5 rounded shadow hover:shadow-md transition-shadow border-l-4 border-gray-500">
          <h2 className="font-bold mb-1">📋 Logs</h2>
          <p className="text-sm text-gray-500">Ver logs detalhados do crawler</p>
        </Link>
      </div>
    </div>
  );
}
