import { useQuery, useMutation } from "@tanstack/react-query";
import { api, useToken } from "../../lib/api";
import AdminNav from "../../components/AdminNav";

export default function Promoter() {
  const token = useToken();

  const { data: logs, isLoading } = useQuery({
    queryKey: ["promotion-logs", token],
    queryFn: () => api.getPromotionLogs(token),
    enabled: !!token,
  });

  const runMutation = useMutation({
    mutationFn: () => api.runPromoter(token),
  });

  return (
    <div>
      <AdminNav />
      <h1 className="text-xl font-bold mb-4">📣 Divulgação (Promoter)</h1>

      <div className="mb-6">
        <button
          onClick={() => runMutation.mutate()}
          disabled={runMutation.isPending}
          className="bg-green-600 text-white px-5 py-2.5 rounded font-semibold hover:bg-green-700 disabled:opacity-50"
        >
          {runMutation.isPending ? "Executando..." : "🚀 Executar Divulgação Agora"}
        </button>
        {runMutation.isSuccess && <span className="ml-3 text-green-600 text-sm">✅ Promoter iniciado em background</span>}
      </div>

      <h2 className="font-bold mb-2">Logs de Envio</h2>
      <div className="bg-white rounded shadow overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-3 py-2 text-left">Data</th>
              <th className="px-3 py-2">Plataforma</th>
              <th className="px-3 py-2">Destino</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2 text-left">Erro</th>
            </tr>
          </thead>
          <tbody>
            {logs?.map((l) => (
              <tr key={l.id} className={`border-t ${l.status === "failed" ? "bg-red-50" : ""}`}>
                <td className="px-3 py-2 text-xs text-gray-500">{new Date(l.sent_at).toLocaleString("pt-BR")}</td>
                <td className="px-3 py-2 text-center">
                  <span className={`text-xs px-2 py-0.5 rounded ${l.platform === "telegram" ? "bg-blue-100 text-blue-700" : "bg-purple-100 text-purple-700"}`}>
                    {l.platform}
                  </span>
                </td>
                <td className="px-3 py-2 text-center text-xs truncate max-w-[150px]">{l.target}</td>
                <td className="px-3 py-2 text-center">{l.status === "success" ? "✅" : "❌"}</td>
                <td className="px-3 py-2 text-xs text-red-500 truncate max-w-[200px]">{l.error_message || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {isLoading && <p className="text-center py-6 text-gray-400">Carregando...</p>}
        {!isLoading && logs?.length === 0 && <p className="text-center py-6 text-gray-400">Nenhum envio registrado</p>}
      </div>
    </div>
  );
}
