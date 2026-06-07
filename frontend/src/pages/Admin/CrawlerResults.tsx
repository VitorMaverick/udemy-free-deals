import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, useToken } from "../../lib/api";
import AdminNav from "../../components/AdminNav";

export default function CrawlerResults() {
  const token = useToken();
  const queryClient = useQueryClient();
  const [modalCourseId, setModalCourseId] = useState<string | null>(null);
  const [affiliateLink, setAffiliateLink] = useState("");

  const { data: courses, isLoading } = useQuery({
    queryKey: ["pending-courses", token],
    queryFn: () => api.getPendingCourses(token),
    enabled: !!token,
  });

  const mutation = useMutation({
    mutationFn: ({ id, link }: { id: string; link: string }) =>
      api.setAffiliateLink(token, id, link),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pending-courses"] });
      queryClient.invalidateQueries({ queryKey: ["admin-stats"] });
      setModalCourseId(null);
      setAffiliateLink("");
    },
  });

  if (isLoading) return <p className="py-10 text-center text-gray-500">Carregando...</p>;

  return (
    <div>
      <AdminNav />
      <h1 className="text-xl font-bold mb-4">🔍 Cursos Detectados (Pending)</h1>
      <p className="text-sm text-gray-500 mb-4">{courses?.length || 0} cursos aguardando link de afiliado</p>

      <div className="bg-white rounded shadow overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-3 py-2 text-left">Título</th>
              <th className="px-3 py-2">Instrutor</th>
              <th className="px-3 py-2">Preço</th>
              <th className="px-3 py-2">Detectado</th>
              <th className="px-3 py-2">Ações</th>
            </tr>
          </thead>
          <tbody>
            {courses?.map((c) => (
              <tr key={c.id} className="border-t hover:bg-gray-50">
                <td className="px-3 py-2 max-w-xs">
                  <a href={c.udemy_url} target="_blank" rel="noopener" className="text-purple-600 hover:underline">
                    {c.title}
                  </a>
                </td>
                <td className="px-3 py-2 text-center text-gray-600">{c.instructor || "—"}</td>
                <td className="px-3 py-2 text-center">
                  <del className="text-gray-400">R${c.original_price.toFixed(2)}</del>
                  <span className="ml-1 text-green-600 font-bold">{c.is_free ? "GRÁTIS" : `R$${c.discount_price.toFixed(2)}`}</span>
                </td>
                <td className="px-3 py-2 text-center text-xs text-gray-500">
                  {new Date(c.detected_at).toLocaleDateString("pt-BR")}
                </td>
                <td className="px-3 py-2 text-center">
                  <button
                    onClick={() => { setModalCourseId(c.id); setAffiliateLink(""); }}
                    className="bg-purple-600 text-white text-xs px-3 py-1 rounded hover:bg-purple-700"
                  >
                    Cadastrar Link
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {courses?.length === 0 && <p className="text-center py-6 text-gray-400">Nenhum curso pendente</p>}
      </div>

      {/* Modal */}
      {modalCourseId && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setModalCourseId(null)}>
          <div className="bg-white rounded-lg p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-4">Cadastrar Link de Afiliado</h2>
            <p className="text-sm text-gray-500 mb-3">Cole o link gerado no Impact/Udemy deep linking tool:</p>
            <input
              type="url"
              value={affiliateLink}
              onChange={(e) => setAffiliateLink(e.target.value)}
              placeholder="https://trk.udemy.com/..."
              className="w-full border rounded px-3 py-2 mb-4"
              autoFocus
            />
            <div className="flex gap-2 justify-end">
              <button onClick={() => setModalCourseId(null)} className="px-4 py-2 border rounded text-sm">Cancelar</button>
              <button
                onClick={() => mutation.mutate({ id: modalCourseId, link: affiliateLink })}
                disabled={!affiliateLink || mutation.isPending}
                className="px-4 py-2 bg-purple-600 text-white rounded text-sm hover:bg-purple-700 disabled:opacity-50"
              >
                {mutation.isPending ? "Salvando..." : "Salvar"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
