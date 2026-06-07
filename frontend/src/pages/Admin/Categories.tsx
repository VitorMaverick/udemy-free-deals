import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, useToken, CategoryCreate } from "../../lib/api";
import AdminNav from "../../components/AdminNav";

export default function Categories() {
  const token = useToken();
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState<CategoryCreate>({ name: "", description: "", telegram_channels: [], discord_webhooks: [], subreddits: [], twitter_keywords: [] });
  const [channelInput, setChannelInput] = useState("");
  const [webhookInput, setWebhookInput] = useState("");

  const { data: categories, isLoading } = useQuery({
    queryKey: ["categories", token],
    queryFn: () => api.getAdminCategories(token),
    enabled: !!token,
  });

  const createMut = useMutation({
    mutationFn: () => editId ? api.updateCategory(token, editId, form) : api.createCategory(token, form),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["categories"] }); resetForm(); },
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => api.deleteCategory(token, id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["categories"] }),
  });

  const resetForm = () => { setShowForm(false); setEditId(null); setForm({ name: "", description: "", telegram_channels: [], discord_webhooks: [], subreddits: [], twitter_keywords: [] }); };

  const startEdit = (cat: any) => {
    setEditId(cat.id);
    setForm({ name: cat.name, description: cat.description, telegram_channels: cat.telegram_channels, discord_webhooks: cat.discord_webhooks, subreddits: cat.subreddits, twitter_keywords: cat.twitter_keywords });
    setShowForm(true);
  };

  const addToList = (field: keyof CategoryCreate, value: string) => {
    if (!value.trim()) return;
    const current = (form[field] as string[]) || [];
    setForm({ ...form, [field]: [...current, value.trim()] });
  };

  const removeFromList = (field: keyof CategoryCreate, idx: number) => {
    const current = (form[field] as string[]) || [];
    setForm({ ...form, [field]: current.filter((_, i) => i !== idx) });
  };

  if (isLoading) return <div><AdminNav /><p className="py-10 text-center text-gray-500">Carregando...</p></div>;

  return (
    <div>
      <AdminNav />
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-xl font-bold">📂 Categorias de Divulgação</h1>
        <button onClick={() => { resetForm(); setShowForm(true); }} className="bg-purple-600 text-white px-4 py-2 rounded text-sm hover:bg-purple-700">
          + Nova Categoria
        </button>
      </div>

      {/* List */}
      <div className="space-y-3 mb-6">
        {categories?.map((cat) => (
          <div key={cat.id} className="bg-white p-4 rounded shadow">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-bold">{cat.name}</h3>
                <p className="text-sm text-gray-500">{cat.description}</p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {cat.telegram_channels.map((ch) => <span key={ch} className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded">📱 {ch}</span>)}
                  {cat.discord_webhooks.map((_, i) => <span key={i} className="bg-purple-100 text-purple-700 text-xs px-2 py-0.5 rounded">🎮 Discord #{i + 1}</span>)}
                  {cat.subreddits.map((s) => <span key={s} className="bg-orange-100 text-orange-700 text-xs px-2 py-0.5 rounded">📰 r/{s}</span>)}
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => startEdit(cat)} className="text-sm text-blue-600 hover:underline">Editar</button>
                <button onClick={() => deleteMut.mutate(cat.id)} className="text-sm text-red-500 hover:underline">Excluir</button>
              </div>
            </div>
          </div>
        ))}
        {categories?.length === 0 && <p className="text-center text-gray-400 py-6">Nenhuma categoria criada</p>}
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 overflow-y-auto p-4" onClick={resetForm}>
          <div className="bg-white rounded-lg p-6 w-full max-w-lg" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-4">{editId ? "Editar" : "Nova"} Categoria</h2>
            <div className="space-y-3">
              <input placeholder="Nome (ex: Python)" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full border rounded px-3 py-2 text-sm" />
              <input placeholder="Descrição" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="w-full border rounded px-3 py-2 text-sm" />

              {/* Telegram */}
              <div>
                <label className="text-xs font-bold text-gray-500">Canais Telegram</label>
                <div className="flex gap-1">
                  <input placeholder="@canal" value={channelInput} onChange={(e) => setChannelInput(e.target.value)} className="flex-1 border rounded px-2 py-1 text-sm" />
                  <button onClick={() => { addToList("telegram_channels", channelInput); setChannelInput(""); }} className="bg-blue-500 text-white px-3 py-1 rounded text-sm">+</button>
                </div>
                <div className="flex flex-wrap gap-1 mt-1">{form.telegram_channels?.map((ch, i) => <span key={i} className="bg-blue-100 text-xs px-2 py-0.5 rounded cursor-pointer" onClick={() => removeFromList("telegram_channels", i)}>{ch} ✕</span>)}</div>
              </div>

              {/* Discord */}
              <div>
                <label className="text-xs font-bold text-gray-500">Webhooks Discord</label>
                <div className="flex gap-1">
                  <input placeholder="https://discord.com/api/webhooks/..." value={webhookInput} onChange={(e) => setWebhookInput(e.target.value)} className="flex-1 border rounded px-2 py-1 text-sm" />
                  <button onClick={() => { addToList("discord_webhooks", webhookInput); setWebhookInput(""); }} className="bg-purple-500 text-white px-3 py-1 rounded text-sm">+</button>
                </div>
                <div className="flex flex-wrap gap-1 mt-1">{form.discord_webhooks?.map((_, i) => <span key={i} className="bg-purple-100 text-xs px-2 py-0.5 rounded cursor-pointer" onClick={() => removeFromList("discord_webhooks", i)}>Webhook #{i + 1} ✕</span>)}</div>
              </div>
            </div>

            <div className="flex gap-2 justify-end mt-4">
              <button onClick={resetForm} className="px-4 py-2 border rounded text-sm">Cancelar</button>
              <button onClick={() => createMut.mutate()} disabled={!form.name || createMut.isPending} className="px-4 py-2 bg-purple-600 text-white rounded text-sm disabled:opacity-50">
                {createMut.isPending ? "Salvando..." : "Salvar"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
