import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, useToken, CategoryCreate, CategoryItem } from "../../lib/api";
import AdminNav from "../../components/AdminNav";

export default function Categories() {
  const token = useToken();
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [detail, setDetail] = useState<CategoryItem | null>(null);
  const [tab, setTab] = useState<"active" | "discover" | "trending">("active");
  const [form, setForm] = useState<CategoryCreate>({ name: "", description: "", telegram_channels: [], discord_webhooks: [], subreddits: [], twitter_keywords: [] });
  const [input, setInput] = useState("");

  const { data: categories } = useQuery({ queryKey: ["categories", token], queryFn: () => api.getAdminCategories(token), enabled: !!token });

  const saveMut = useMutation({
    mutationFn: () => editId ? api.updateCategory(token, editId, form) : api.createCategory(token, form),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["categories"] }); setShowForm(false); setEditId(null); },
  });
  const deleteMut = useMutation({ mutationFn: (id: string) => api.deleteCategory(token, id), onSuccess: () => qc.invalidateQueries({ queryKey: ["categories"] }) });
  const discoverMut = useMutation({ mutationFn: (id: string) => api.discoverCommunities(token, id) });
  const addCommMut = useMutation({
    mutationFn: (p: { id: string; platform: string; value: string }) => api.addCommunity(token, p.id, p.platform, p.value),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["categories"] }),
  });
  const trendingMut = useMutation({ mutationFn: (id: string) => api.getTrendingPosts(token, id) });
  const commentMut = useMutation({ mutationFn: (body: any) => api.generateComment(token, body) });

  const openEdit = (cat: CategoryItem) => {
    setEditId(cat.id); setForm({ name: cat.name, description: cat.description, telegram_channels: cat.telegram_channels, discord_webhooks: cat.discord_webhooks, subreddits: cat.subreddits || [], twitter_keywords: cat.twitter_keywords || [] }); setShowForm(true);
  };

  const addToField = (field: keyof CategoryCreate) => { if (!input.trim()) return; const arr = (form[field] as string[]) || []; setForm({ ...form, [field]: [...arr, input.trim()] }); setInput(""); };
  const rmFromField = (field: keyof CategoryCreate, i: number) => { const arr = (form[field] as string[]) || []; setForm({ ...form, [field]: arr.filter((_, idx) => idx !== i) }); };

  return (
    <div>
      <AdminNav />
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-xl font-bold">📂 Categorias</h1>
        <button onClick={() => { setEditId(null); setForm({ name: "", description: "", telegram_channels: [], discord_webhooks: [], subreddits: [], twitter_keywords: [] }); setShowForm(true); }} className="bg-purple-600 text-white px-4 py-2 rounded text-sm">+ Nova</button>
      </div>

      {/* Category List */}
      <div className="grid gap-3 mb-6">
        {categories?.map((cat) => (
          <div key={cat.id} className="bg-white p-4 rounded shadow cursor-pointer hover:shadow-md" onClick={() => { setDetail(cat); setTab("active"); }}>
            <div className="flex justify-between">
              <div>
                <h3 className="font-bold">{cat.name}</h3>
                <div className="flex gap-1 mt-1 flex-wrap">
                  {cat.telegram_channels?.map((c) => <span key={c} className="bg-blue-100 text-blue-700 text-xs px-1.5 py-0.5 rounded">📱{c}</span>)}
                  {cat.discord_webhooks?.map((_, i) => <span key={i} className="bg-purple-100 text-purple-700 text-xs px-1.5 py-0.5 rounded">🎮 Discord</span>)}
                  {cat.subreddits?.map((s) => <span key={s} className="bg-orange-100 text-orange-700 text-xs px-1.5 py-0.5 rounded">r/{s}</span>)}
                </div>
              </div>
              <div className="flex gap-2 text-sm">
                <button onClick={(e) => { e.stopPropagation(); openEdit(cat); }} className="text-blue-600 hover:underline">Editar</button>
                <button onClick={(e) => { e.stopPropagation(); deleteMut.mutate(cat.id); }} className="text-red-500 hover:underline">Excluir</button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Detail Panel */}
      {detail && (
        <div className="bg-white rounded shadow p-5">
          <div className="flex justify-between items-center mb-4">
            <h2 className="font-bold text-lg">{detail.name}</h2>
            <button onClick={() => setDetail(null)} className="text-gray-400 text-sm">✕ Fechar</button>
          </div>
          {/* Tabs */}
          <div className="flex gap-2 mb-4 border-b pb-2">
            {(["active", "discover", "trending"] as const).map((t) => (
              <button key={t} onClick={() => setTab(t)} className={`px-3 py-1 rounded text-sm ${tab === t ? "bg-purple-600 text-white" : "bg-gray-100"}`}>
                {t === "active" ? "🔊 Canais Ativos" : t === "discover" ? "🔍 Descobrir" : "🔥 Trending"}
              </button>
            ))}
          </div>

          {/* Active Tab */}
          {tab === "active" && (
            <div className="space-y-2 text-sm">
              <p className="font-semibold">Telegram:</p>
              {detail.telegram_channels?.map((ch) => <span key={ch} className="inline-block bg-blue-50 px-2 py-1 rounded mr-1">{ch}</span>)}
              <p className="font-semibold mt-2">Discord:</p>
              {detail.discord_webhooks?.length ? <span className="text-gray-500">{detail.discord_webhooks.length} webhook(s) configurado(s)</span> : <span className="text-gray-400">Nenhum</span>}
              <p className="font-semibold mt-2">Reddit:</p>
              {detail.subreddits?.map((s) => <span key={s} className="inline-block bg-orange-50 px-2 py-1 rounded mr-1">r/{s}</span>)}
              {!detail.telegram_channels?.length && !detail.discord_webhooks?.length && !detail.subreddits?.length && <p className="text-gray-400">Nenhum canal ativo. Use a aba "Descobrir" para encontrar.</p>}
            </div>
          )}

          {/* Discover Tab */}
          {tab === "discover" && (
            <div>
              <button onClick={() => discoverMut.mutate(detail.id)} disabled={discoverMut.isPending} className="bg-blue-600 text-white px-4 py-2 rounded text-sm mb-4 disabled:opacity-50">
                {discoverMut.isPending ? "Buscando..." : "🔍 Buscar Comunidades"}
              </button>
              {discoverMut.data && (
                <div className="space-y-3">
                  {discoverMut.data.telegram?.length > 0 && (
                    <div>
                      <p className="font-semibold text-sm mb-1">Telegram:</p>
                      {discoverMut.data.telegram.map((ch: any) => (
                        <div key={ch.username} className="flex justify-between items-center bg-gray-50 p-2 rounded mb-1">
                          <span className="text-sm">{ch.username} <span className="text-gray-400">({ch.members} membros)</span></span>
                          <button onClick={() => addCommMut.mutate({ id: detail.id, platform: "telegram", value: ch.username })} className="text-xs bg-green-500 text-white px-2 py-1 rounded">+ Adicionar</button>
                        </div>
                      ))}
                    </div>
                  )}
                  {discoverMut.data.reddit?.length > 0 && (
                    <div>
                      <p className="font-semibold text-sm mb-1">Reddit:</p>
                      {discoverMut.data.reddit.map((s: any) => (
                        <div key={s.name} className="flex justify-between items-center bg-gray-50 p-2 rounded mb-1">
                          <span className="text-sm">r/{s.name} <span className="text-gray-400">({s.subscribers?.toLocaleString()} subs)</span></span>
                          <button onClick={() => addCommMut.mutate({ id: detail.id, platform: "reddit", value: s.name })} className="text-xs bg-green-500 text-white px-2 py-1 rounded">+ Adicionar</button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Trending Tab */}
          {tab === "trending" && (
            <div>
              <button onClick={() => trendingMut.mutate(detail.id)} disabled={trendingMut.isPending} className="bg-orange-500 text-white px-4 py-2 rounded text-sm mb-4 disabled:opacity-50">
                {trendingMut.isPending ? "Buscando..." : "🔥 Buscar Posts em Alta"}
              </button>
              {trendingMut.data && (
                <div className="space-y-4">
                  {trendingMut.data.reddit?.length > 0 && (
                    <div>
                      <p className="font-semibold text-sm mb-1">Reddit:</p>
                      {trendingMut.data.reddit.slice(0, 5).map((p: any) => (
                        <div key={p.id} className="bg-gray-50 p-2 rounded mb-2">
                          <a href={p.url} target="_blank" rel="noopener" className="text-sm text-blue-600 hover:underline">{p.title}</a>
                          <div className="text-xs text-gray-500 mt-1">r/{p.subreddit} · ⬆️{p.score} · 💬{p.num_comments}</div>
                          <button onClick={() => commentMut.mutate({ post: p, category_name: detail.name, affiliate_link: "", course_title: "" })} className="text-xs text-purple-600 mt-1 hover:underline">💬 Gerar Comentário</button>
                        </div>
                      ))}
                    </div>
                  )}
                  {trendingMut.data.twitter?.length > 0 && !trendingMut.data.twitter[0]?.error && (
                    <div>
                      <p className="font-semibold text-sm mb-1">Twitter:</p>
                      {trendingMut.data.twitter.slice(0, 5).map((t: any) => (
                        <div key={t.id} className="bg-gray-50 p-2 rounded mb-2">
                          <p className="text-sm">{t.text?.slice(0, 150)}</p>
                          <div className="text-xs text-gray-500 mt-1">@{t.author} · ❤️{t.likes} · 🔄{t.retweets}</div>
                          <a href={t.url} target="_blank" rel="noopener" className="text-xs text-blue-600 hover:underline">Ver tweet</a>
                        </div>
                      ))}
                    </div>
                  )}
                  {trendingMut.data.twitter?.[0]?.error && <p className="text-xs text-gray-400">{trendingMut.data.twitter[0].error}</p>}
                </div>
              )}
              {commentMut.data && (
                <div className="mt-4 bg-yellow-50 p-3 rounded border border-yellow-200">
                  <p className="text-xs font-bold mb-1">Comentário sugerido (copie e cole):</p>
                  <p className="text-sm">{commentMut.data.comment}</p>
                  <button onClick={() => navigator.clipboard.writeText(commentMut.data?.comment || "")} className="text-xs text-purple-600 mt-1 hover:underline">📋 Copiar</button>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Create/Edit Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowForm(false)}>
          <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-4">{editId ? "Editar" : "Nova"} Categoria</h2>
            <div className="space-y-3">
              <input placeholder="Nome" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full border rounded px-3 py-2 text-sm" />
              <input placeholder="Descrição" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="w-full border rounded px-3 py-2 text-sm" />
              {/* Dynamic lists */}
              {(["telegram_channels", "discord_webhooks", "subreddits", "twitter_keywords"] as const).map((field) => (
                <div key={field}>
                  <label className="text-xs font-bold text-gray-500">{field.replace("_", " ")}</label>
                  <div className="flex gap-1">
                    <input placeholder={`Adicionar ${field}`} value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") { addToField(field); } }} className="flex-1 border rounded px-2 py-1 text-sm" />
                    <button onClick={() => addToField(field)} className="bg-gray-200 px-3 py-1 rounded text-sm">+</button>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-1">{(form[field] as string[])?.map((v, i) => <span key={i} className="bg-gray-100 text-xs px-2 py-0.5 rounded cursor-pointer hover:bg-red-100" onClick={() => rmFromField(field, i)}>{v} ✕</span>)}</div>
                </div>
              ))}
            </div>
            <div className="flex gap-2 justify-end mt-4">
              <button onClick={() => setShowForm(false)} className="px-4 py-2 border rounded text-sm">Cancelar</button>
              <button onClick={() => saveMut.mutate()} disabled={!form.name} className="px-4 py-2 bg-purple-600 text-white rounded text-sm disabled:opacity-50">Salvar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
