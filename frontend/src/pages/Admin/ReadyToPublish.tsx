import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, useToken } from "../../lib/api";
import AdminNav from "../../components/AdminNav";

export default function ReadyToPublish() {
  const token = useToken();
  const queryClient = useQueryClient();

  const { data: courses, isLoading } = useQuery({
    queryKey: ["ready-courses", token],
    queryFn: () => api.getReadyCourses(token),
    enabled: !!token,
  });

  const publishMutation = useMutation({
    mutationFn: () => api.publishToday(token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ready-courses"] });
      queryClient.invalidateQueries({ queryKey: ["admin-stats"] });
    },
  });

  if (isLoading) return <p className="py-10 text-center text-gray-500">Carregando...</p>;

  return (
    <div>
      <AdminNav />
      <h1 className="text-xl font-bold mb-4">✅ Cursos com Link Cadastrado</h1>
      <p className="text-sm text-gray-500 mb-4">{courses?.length || 0} cursos prontos para publicação</p>

      {courses && courses.length > 0 && (
        <div className="mb-6">
          <button
            onClick={() => publishMutation.mutate()}
            disabled={publishMutation.isPending}
            className="bg-green-600 text-white px-5 py-2.5 rounded font-semibold hover:bg-green-700 disabled:opacity-50"
          >
            {publishMutation.isPending ? "Publicando..." : "📰 Publicar Post do Dia"}
          </button>
          {publishMutation.isSuccess && (
            <p className="mt-3 text-green-600 text-sm font-medium">
              ✅ Post publicado com sucesso! ({publishMutation.data?.courses?.length} cursos)
            </p>
          )}
          {publishMutation.isError && (
            <p className="mt-3 text-red-500 text-sm">Erro ao publicar</p>
          )}
        </div>
      )}

      <div className="bg-white rounded shadow overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-3 py-2 text-left">Título</th>
              <th className="px-3 py-2">Link de Afiliado</th>
              <th className="px-3 py-2">Cadastrado em</th>
            </tr>
          </thead>
          <tbody>
            {courses?.map((c) => (
              <tr key={c.id} className="border-t hover:bg-gray-50">
                <td className="px-3 py-2 max-w-xs truncate">{c.title}</td>
                <td className="px-3 py-2 text-center">
                  <a href={c.affiliate_link} target="_blank" rel="noopener" className="text-purple-600 text-xs hover:underline truncate block max-w-[200px] mx-auto">
                    {c.affiliate_link.slice(0, 50)}...
                  </a>
                </td>
                <td className="px-3 py-2 text-center text-xs text-gray-500">
                  {c.manual_link_created_at ? new Date(c.manual_link_created_at).toLocaleString("pt-BR") : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {courses?.length === 0 && <p className="text-center py-6 text-gray-400">Nenhum curso pronto</p>}
      </div>
    </div>
  );
}
