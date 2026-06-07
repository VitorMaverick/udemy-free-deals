import { useQuery } from "@tanstack/react-query";
import { api, useToken } from "../../lib/api";
import AdminNav from "../../components/AdminNav";

export default function Logs() {
  const token = useToken();

  const { data: logs, isLoading } = useQuery({
    queryKey: ["admin-logs", token],
    queryFn: () => api.getLogs(token),
    enabled: !!token,
    refetchInterval: 5000, // Auto-refresh a cada 5s
  });

  if (isLoading) return <p className="py-10 text-center text-gray-500">Carregando...</p>;

  return (
    <div>
      <AdminNav />
      <h1 className="text-xl font-bold mb-4">📋 Logs do Crawler</h1>
      <div className="bg-white rounded shadow overflow-x-auto max-h-[70vh] overflow-y-auto">
        <table className="w-full text-xs font-mono">
          <thead className="bg-gray-100 sticky top-0">
            <tr>
              <th className="px-3 py-2 text-left">Data</th>
              <th className="px-3 py-2 text-left">Nível</th>
              <th className="px-3 py-2 text-left">Mensagem</th>
            </tr>
          </thead>
          <tbody>
            {logs?.map((l) => (
              <tr key={l.id} className={`border-t ${l.level === "ERROR" ? "bg-red-50" : ""}`}>
                <td className="px-3 py-1.5 text-gray-500 whitespace-nowrap">
                  {new Date(l.created_at).toLocaleString("pt-BR")}
                </td>
                <td className={`px-3 py-1.5 font-bold ${l.level === "ERROR" ? "text-red-600" : "text-blue-600"}`}>
                  {l.level}
                </td>
                <td className="px-3 py-1.5">{l.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {logs?.length === 0 && <p className="text-center py-6 text-gray-400">Nenhum log</p>}
      </div>
    </div>
  );
}
