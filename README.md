# 🎓 Udemy Free Deals

Um site que descobre e lista diariamente cursos da Udemy que estão **temporariamente gratuitos (100% off)**, usando links de afiliado para monetização.

O sistema roda um **crawler automático** a cada 6 horas que busca cursos gratuitos em sites agregadores de cupons. O admin revisa os cursos encontrados, cadastra os links de afiliado manualmente, e publica o "post do dia" com os melhores deals.

---

## 🏗️ Como funciona

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│   Visitante  │────▶│  App (Fly.io)    │────▶│  Supabase    │
│  (navegador) │     │  FastAPI + React  │     │  PostgreSQL  │
└──────────────┘     └────────┬─────────┘     └──────────────┘
                              │
                     ┌────────▼─────────┐
                     │   Crawler (auto) │
                     │  a cada 6 horas  │
                     └────────┬─────────┘
                              │
                     ┌────────▼─────────┐
                     │  Sites de cupons │
                     │  (discudemy etc) │
                     └──────────────────┘
```

**Fluxo do admin:**
1. Crawler encontra cursos gratuitos → status `pending`
2. Admin acessa `/admin`, vê os cursos detectados
3. Admin gera link de afiliado no Impact/Udemy e cadastra no sistema → status `manual_link_created`
4. Admin clica "Publicar Post do Dia" → status `published` (visível no site)

---

## 🛠️ Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, APScheduler |
| Crawler | httpx, BeautifulSoup4 |
| Frontend | React 18, TypeScript, Vite, TailwindCSS, TanStack Query |
| Banco | PostgreSQL (Supabase) / SQLite (dev local) |
| Auth | JWT (python-jose) + bcrypt |
| Deploy | Fly.io (grátis) |

---

## 🚀 Rodar Localmente (Desenvolvimento)

### Pré-requisitos
- Python 3.11+
- Node.js 18+
- Git

### 1. Clonar o projeto

```bash
git clone <url-do-repo>
cd udemy-free-deals
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Linux/Mac
# .\venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

Agora inicie o servidor:

```bash
uvicorn app.main:app --reload --port 8000
```

O backend vai:
- Criar o banco SQLite automaticamente (`dev.db`)
- Criar o usuário admin padrão (login: `admin`, senha: `admin123`)
- Iniciar o scheduler do crawler

Teste: abra http://localhost:8000/api/health → deve retornar `{"status":"ok"}`

### 3. Frontend

Abra outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Acesse: http://localhost:5173

### 4. Testar o sistema

1. Acesse http://localhost:5173/admin
2. Faça login com `admin` / `admin123`
3. No dashboard, clique "🔄 Rodar Crawler"
4. Aguarde ~1 minuto e vá em "Cursos Detectados" para ver os cursos encontrados

---

## ☁️ Deploy em Produção (Grátis)

O deploy usa **Fly.io** (hospedagem) + **Supabase** (banco de dados). **Custo total: R$ 0,00/mês**.

### Como funciona o custo zero

| Serviço | O que faz | Custo |
|---------|-----------|-------|
| Fly.io | Roda o servidor (backend + frontend) | Grátis (US$ 5/mês de crédito cobre tudo) |
| Supabase | Banco de dados PostgreSQL na nuvem | Grátis (500 MB inclusos) |

> ⚠️ **Sobre a Fly.io:** pede cartão de crédito no cadastro, mas **não cobra** enquanto você usar menos de US$ 5/mês. Com nosso app (1 máquina de 256MB), o custo é ~US$ 1,94/mês, totalmente coberto pelo crédito gratuito.

---

### Passo 1: Criar o banco de dados no Supabase

1. Acesse [supabase.com](https://supabase.com) e crie uma conta (grátis, sem cartão)
2. Clique em **"New Project"**
3. Preencha:
   - **Nome:** `udemy-free-deals`
   - **Senha do banco:** escolha uma senha forte e **anote ela**
   - **Região:** South America (São Paulo)
4. Aguarde o projeto ser criado (~1 minuto)
5. No menu lateral, vá em **Project Settings → Database**
6. Na seção **"Connection string"**, clique na aba **"URI"**
7. Copie a URL. Ela vai ser algo assim:
   ```
   postgresql://postgres.[codigo]:SUASENHA@aws-0-sa-east-1.pooler.supabase.com:5432/postgres
   ```
   (Substitua `[YOUR-PASSWORD]` pela senha que você definiu no passo 3)

**Guarde essa URL** — você vai usar no próximo passo.

---

### Passo 2: Instalar o Fly.io CLI

No terminal:

```bash
# Linux/Mac
curl -L https://fly.io/install.sh | sh

# Depois, crie uma conta ou faça login
fly auth signup
# ou
fly auth login
```

---

### Passo 3: Fazer o deploy

Na pasta do projeto, rode:

```bash
cd udemy-free-deals
./deploy.sh
```

O script vai perguntar:
1. **DATABASE_URL** — cole a URL do Supabase (passo 1)
2. **SECRET_KEY** — aperte Enter (gera automaticamente)
3. **ADMIN_USERNAME** — aperte Enter para usar `admin`
4. **ADMIN_PASSWORD** — digite uma senha forte para o painel admin

Aguarde o deploy (~3 minutos). No final ele mostra o link do site.

---

### Passo 4: Acessar o site

- **Site público:** https://udemy-free-deals.fly.dev
- **Painel admin:** https://udemy-free-deals.fly.dev/admin

---

### Se o `deploy.sh` não funcionar

Você pode fazer manualmente:

```bash
# 1. Criar o app
fly apps create udemy-free-deals

# 2. Configurar as variáveis (cole a URL do Supabase e escolha uma senha)
fly secrets set DATABASE_URL="postgresql://postgres.xxx:SENHA@aws-0-sa-east-1.pooler.supabase.com:5432/postgres" SECRET_KEY="$(openssl rand -hex 32)" ADMIN_USERNAME="admin" ADMIN_PASSWORD="SuaSenhaAqui" --app udemy-free-deals

# 3. Deploy
fly deploy
```

---

## 🔧 Comandos Úteis

```bash
# Ver logs do servidor (útil para debugar)
fly logs --app udemy-free-deals

# Atualizar o app depois de mudar o código
fly deploy

# Mudar uma variável de ambiente (reinicia o app automaticamente)
fly secrets set ADMIN_PASSWORD="NovaSenha123" --app udemy-free-deals

# Ver quanto está gastando
fly billing view
```

---

## 📁 Estrutura do Projeto

```
udemy-free-deals/
├── backend/
│   ├── app/
│   │   ├── main.py           # Entrada da aplicação FastAPI
│   │   ├── config.py         # Configurações e variáveis de ambiente
│   │   ├── database.py       # Conexão com o banco
│   │   ├── models.py         # Tabelas do banco (Course, Post, Log, etc.)
│   │   ├── schemas.py        # Validação de dados (Pydantic)
│   │   ├── auth.py           # Autenticação JWT
│   │   ├── crawler/
│   │   │   └── udemy_crawler.py  # Crawler que busca cursos gratuitos
│   │   ├── routers/
│   │   │   ├── admin.py      # Endpoints do painel admin
│   │   │   ├── courses.py    # Endpoints públicos de cursos
│   │   │   └── posts.py      # Endpoints de posts
│   │   └── services/
│   │       └── scheduler.py  # Agendador automático do crawler
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/            # Páginas (Home, Admin, etc.)
│   │   ├── components/       # Componentes reutilizáveis
│   │   └── lib/api.ts        # Cliente HTTP para a API
│   ├── package.json
│   └── vite.config.ts
├── Dockerfile                # Receita para montar o container
├── fly.toml                  # Configuração do Fly.io
├── entrypoint.sh             # Script que inicia o servidor
├── deploy.sh                 # Script helper para deploy
└── monitor.sh                # Script de monitoramento local
```

---

## 📣 Configuração do Módulo Promotor (Divulgação Automática)

O promotor envia cursos publicados para canais do Telegram e Discord automaticamente, e permite descobrir comunidades e trending posts para divulgação semi-automática.

### Obter Credenciais de Cada Plataforma

#### 🤖 Telegram Bot

1. Abra o Telegram e converse com [@BotFather](https://t.me/BotFather)
2. Envie `/newbot`, escolha nome e username
3. Copie o token (ex: `7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxx`)
4. **Adicione o bot como administrador** no canal onde quer postar
5. Configure:
   ```bash
   fly secrets set TELEGRAM_BOT_TOKEN="7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxx" --app udemy-free-deals
   ```

#### 🐦 Twitter API v2 (para busca de trending posts)

1. Acesse [developer.twitter.com](https://developer.twitter.com/en/portal/dashboard)
2. Crie um projeto e app
3. Gere o **Bearer Token** (aba Keys and Tokens)
4. Configure:
   ```bash
   fly secrets set TWITTER_BEARER_TOKEN="AAAAAAAAAAAAAAAAAAAAAxxxxxxxx" --app udemy-free-deals
   ```

> Twitter é usado **apenas para buscar posts em alta** — não posta nada automaticamente.

#### 🟠 Reddit API (para busca de comunidades e trending posts)

1. Acesse [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Clique "create another app" → selecione **"script"**
3. Preencha nome e redirect URI (`http://localhost:8080`)
4. Copie o `client_id` (string abaixo do nome do app) e `client_secret`
5. Configure:
   ```bash
   fly secrets set REDDIT_CLIENT_ID="xxxxxx" REDDIT_CLIENT_SECRET="xxxxxx" --app udemy-free-deals
   ```

> Reddit funciona sem credenciais para buscas (usa API pública). Credenciais são necessárias apenas para postagem automática em subreddits.

#### 🎮 Discord Webhook

1. No Discord, vá no canal → **Configurações** → **Integrações** → **Webhooks** → **Novo Webhook**
2. Copie a URL (ex: `https://discord.com/api/webhooks/1234.../abcdef...`)
3. No admin do site, vá em **📂 Categorias** → edite uma categoria → adicione a URL no campo "discord_webhooks"

> Discord não precisa de variável de ambiente — os webhooks ficam cadastrados por categoria.

### Variáveis de Ambiente Completas

Adicione ao `.env` (local) ou configure via `fly secrets set` (produção):

```env
# === OBRIGATÓRIOS ===
DATABASE_URL=postgresql://...          # URL do Supabase
SECRET_KEY=string-aleatoria-longa      # openssl rand -hex 32
ADMIN_USERNAME=admin
ADMIN_PASSWORD=SuaSenhaForte

# === PROMOTOR (configurar conforme necessidade) ===
TELEGRAM_BOT_TOKEN=                    # Token do @BotFather
TWITTER_BEARER_TOKEN=                  # Para busca de trending posts
REDDIT_CLIENT_ID=                      # Para busca/postagem Reddit
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=UdemyFreeDeals/1.0

# === OPCIONAIS ===
CRAWLER_INTERVAL_HOURS=6               # Intervalo do crawler (padrão 6h)
CORS_ORIGINS=https://udemy-free-deals.fly.dev
```

### Fluxo de Uso Completo

1. **Criar categoria** → `/admin/categories` (ex: "Python")
2. **Adicionar canais** — Telegram, Discord webhooks, subreddits
3. **Descobrir comunidades** — clique na categoria → aba "🔍 Descobrir" → "Buscar Comunidades" → "Adicionar"
4. **Associar cursos** — na listagem de cursos, selecione a categoria
5. **Divulgar** → `/admin/promoter` → "🚀 Executar Divulgação Agora"
6. **Trending posts** → clique na categoria → aba "🔥 Trending" → gera comentários para copiar/colar manualmente
7. **Ver logs** → na página Promoter, tabela mostra sucesso/falha de cada envio

### Scheduler Automático

| Job | Frequência | O que faz |
|-----|-----------|-----------|
| Crawler | A cada 6 horas | Busca cursos gratuitos em sites de cupons |
| Promoter | Todo dia às 10h | Divulga cursos publicados nos canais da categoria |

Para alterar horários, edite `backend/app/services/scheduler.py`.

---

## ☁️ Comandos de Deploy (Fly.io)

```bash
# Listar secrets atuais
fly secrets list --app udemy-free-deals

# Adicionar/atualizar secrets do promotor
fly secrets set \
  TELEGRAM_BOT_TOKEN="seu_token" \
  TWITTER_BEARER_TOKEN="seu_bearer" \
  REDDIT_CLIENT_ID="seu_client_id" \
  REDDIT_CLIENT_SECRET="seu_secret" \
  --app udemy-free-deals

# Deploy (rebuild com código novo)
fly deploy --app udemy-free-deals

# Verificar se o scheduler iniciou
fly logs --app udemy-free-deals
```

---

## ✅ Checklist Pós-Deploy

- [ ] Site carrega em `https://udemy-free-deals.fly.dev`
- [ ] Login admin funciona
- [ ] Crawler encontra cursos (clique "Rodar Crawler" no dashboard)
- [ ] Categoria criada com canais Telegram/Discord
- [ ] Curso publicado associado à categoria
- [ ] "Executar Divulgação" envia mensagem pro Telegram/Discord
- [ ] Logs de envio aparecem em `/admin/promoter`
- [ ] "Descobrir Comunidades" retorna resultados (Reddit funciona sem credenciais)
- [ ] "Trending Posts" funciona (precisa de TWITTER_BEARER_TOKEN para Twitter)

---

## 🐛 Problemas Comuns

| Problema | Causa | Solução |
|----------|-------|---------|
| App reinicia em loop no Fly.io | `DATABASE_URL` errada | Verifique se a senha está correta na URL do Supabase |
| `ModuleNotFoundError: psycopg2` | URL sem prefixo correto | Já corrigido no código — basta fazer `fly deploy` de novo |
| Crawler encontra 0 cursos | IPs de cloud bloqueados por sites | Normal para alguns sites. O discudemy costuma funcionar |
| "502 Bad Gateway" | App não iniciou ainda | Espere 30 segundos e tente de novo |
| Login não funciona | SECRET_KEY não configurada | `fly secrets set SECRET_KEY="$(openssl rand -hex 32)" --app udemy-free-deals` |

---

## 📝 Licença

Projeto pessoal/educacional.
