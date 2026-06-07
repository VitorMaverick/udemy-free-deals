# 🚀 Deploy Gratuito – Udemy Free Deals

## Arquitetura (R$ 0,00/mês)

| Componente | Serviço | Custo | Limite |
|-----------|---------|-------|--------|
| Backend + Frontend | Fly.io (1 VM shared, 256MB) | US$ 0 (coberto pelo crédito de US$5/mês) | 1 app |
| Banco de dados | Supabase (PostgreSQL) | US$ 0 | 500 MB, 50k rows |
| Scheduler | APScheduler (interno) + cron-job.org (backup) | US$ 0 | — |
| Domínio | `udemy-free-deals.fly.dev` | US$ 0 | — |

**Total mensal: R$ 0,00** (enquanto uso ficar dentro dos limites gratuitos)

---

## ⚠️ Aviso sobre Fly.io

A Fly.io exige cadastro de cartão de crédito para ativar a conta Hobby. **Não cobra** enquanto o uso ficar abaixo de US$ 5,00/mês. Com 1 VM de 256MB (~US$ 1,94/mês), você fica bem dentro do crédito.

**Alternativas sem cartão:**
- **Render.com** – free tier (suspende após 15min de inatividade)
- **Railway** – US$ 5 crédito inicial (cobra depois)

---

## 📁 Arquivos de Deploy

### 1. `Dockerfile`

```dockerfile
# Stage 1: Build frontend
FROM node:20-alpine AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY --from=frontend /build/dist /app/static
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8080
ENTRYPOINT ["./entrypoint.sh"]
```

### 2. `fly.toml`

```toml
app = 'udemy-free-deals'
primary_region = 'gru'

[build]

[env]
  CORS_ORIGINS = "https://udemy-free-deals.fly.dev"
  CRAWLER_INTERVAL_HOURS = "6"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = 'stop'
  auto_start_machines = true
  min_machines_running = 1

[[vm]]
  memory = '256mb'
  cpu_kind = 'shared'
  cpus = 1
```

### 3. `entrypoint.sh`

```bash
#!/bin/sh
set -e
echo "Criando tabelas..."
python -c "
from app.database import Base, engine
import asyncio
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init())
"
echo "Iniciando servidor..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### 4. `.dockerignore`

```
**/__pycache__
**/node_modules
**/dist
**/.env
**/venv
**/.git
**/dev.db
**/logs
```

### 5. `deploy.sh`

```bash
#!/bin/bash
set -e

APP="udemy-free-deals"

echo "🚀 Deploy Gratuito - Udemy Free Deals"
echo "======================================"

# Verificações
command -v fly >/dev/null || { echo "❌ Instale flyctl: curl -L https://fly.io/install.sh | sh"; exit 1; }
fly auth whoami >/dev/null 2>&1 || { echo "❌ Faça login: fly auth login"; exit 1; }

# Criar app
if ! fly apps list 2>/dev/null | grep -q "$APP"; then
    echo "📦 Criando app..."
    fly apps create "$APP"
fi

# Secrets
echo ""
echo "🔐 Configurar secrets (pule com Enter se já configurados)"
read -p "DATABASE_URL do Supabase (postgresql://...): " DB_URL
read -p "SECRET_KEY (deixe vazio para gerar): " SECRET
SECRET=${SECRET:-$(openssl rand -hex 32)}
read -p "ADMIN_USERNAME [admin]: " ADMIN_USER
ADMIN_USER=${ADMIN_USER:-admin}
read -sp "ADMIN_PASSWORD: " ADMIN_PASS
echo ""

if [ -n "$DB_URL" ]; then
    fly secrets set \
        DATABASE_URL="$DB_URL" \
        SECRET_KEY="$SECRET" \
        ADMIN_USERNAME="$ADMIN_USER" \
        ADMIN_PASSWORD="$ADMIN_PASS" \
        --app "$APP"
fi

# Deploy
echo "🚀 Deploying..."
fly deploy --app "$APP"

echo ""
echo "✅ Pronto! https://${APP}.fly.dev"
```

### 6. `frontend/.env.production`

```
VITE_API_URL=
```

### 7. `backend/requirements.txt` (adicionar psycopg2)

Garanta que `psycopg2-binary` está no requirements para conectar ao Supabase:
```
asyncpg==0.29.0
```
(já está incluído no projeto)

---

## 📋 Instruções Passo a Passo

### Etapa 1: Criar banco no Supabase (5 min)

1. Acesse [supabase.com](https://supabase.com) e crie uma conta (grátis, sem cartão)
2. Clique **"New Project"**
3. Escolha:
   - Nome: `udemy-free-deals`
   - Senha do banco: anote (vai usar na URL)
   - Região: **South America (São Paulo)**
4. Após criar, vá em **Settings → Database → Connection string → URI**
5. Copie a URL e substitua `[YOUR-PASSWORD]` pela senha que definiu
6. O formato será: `postgresql://postgres.[ref]:[senha]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres`

**⚠️ Use a porta `5432` (direct) ao invés de `6543` (pooler) se tiver problemas com SQLAlchemy async.**

Para usar com asyncpg, troque `postgresql://` por `postgresql+asyncpg://`:
```
postgresql+asyncpg://postgres.[ref]:[senha]@aws-0-sa-east-1.pooler.supabase.com:5432/postgres
```

### Etapa 2: Instalar Fly.io CLI

```bash
curl -L https://fly.io/install.sh | sh
fly auth signup   # ou fly auth login
```

### Etapa 3: Deploy

```bash
cd ~/repo/udemy-free-deals
chmod +x deploy.sh entrypoint.sh
./deploy.sh
```

Ou manualmente:

```bash
# Criar app
fly apps create udemy-free-deals

# Configurar secrets
fly secrets set \
  DATABASE_URL="postgresql+asyncpg://postgres.xxx:senha@aws-0-sa-east-1.pooler.supabase.com:5432/postgres" \
  SECRET_KEY="$(openssl rand -hex 32)" \
  ADMIN_USERNAME="admin" \
  ADMIN_PASSWORD="SuaSenhaForte" \
  CORS_ORIGINS="https://udemy-free-deals.fly.dev" \
  --app udemy-free-deals

# Deploy
fly deploy
```

### Etapa 4: Verificar

```bash
# Logs
fly logs --app udemy-free-deals

# Testar
curl https://udemy-free-deals.fly.dev/api/health
# → {"status":"ok"}

# Acessar frontend
# https://udemy-free-deals.fly.dev
```

### Etapa 5 (Opcional): Cron externo para o crawler

Para garantir que o crawler roda mesmo se o scheduler interno falhar:

1. Acesse [cron-job.org](https://cron-job.org) (grátis)
2. Crie um job:
   - URL: `https://udemy-free-deals.fly.dev/api/admin/crawler/run`
   - Método: POST
   - Headers: `Authorization: Bearer SEU_TOKEN_JWT`
   - Schedule: A cada 6 horas (`0 */6 * * *`)

Para gerar o token:
```bash
curl -X POST https://udemy-free-deals.fly.dev/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"SuaSenhaForte"}'
```

---

## 🔧 Solução de Problemas

| Problema | Causa | Solução |
|----------|-------|---------|
| `connection refused` no banco | URL errada ou porta errada | Use porta `5432` (não 6543). Prefixe com `postgresql+asyncpg://` |
| App reinicia em loop | Migração falha | Verifique `fly logs`. Provavelmente a DATABASE_URL está errada |
| `502 Bad Gateway` | App não inicia a tempo | Aumente memory para 512mb no fly.toml se necessário |
| Crawler retorna 0 cursos | Sites bloqueando IP da Fly | Normal — use cron-job.org para testar. IPs de cloud são frequentemente bloqueados |
| `out of memory` | 256MB insuficiente | Troque para `memory = '512mb'` no fly.toml (ainda dentro dos US$5) |
| `SSL: certificate verify failed` | asyncpg SSL issue | Adicione `?sslmode=require` na DATABASE_URL |

### Verificar uso de crédito:
```bash
fly billing view
```

### Monitorar tamanho do banco (Supabase):
- Dashboard → Database → Storage Used (limite: 500 MB)

---

## 💰 Resumo de Custos

| Item | Custo/mês |
|------|-----------|
| Fly.io VM 256MB (1 app) | ~US$ 1,94 (coberto pelos US$ 5 de crédito) |
| Supabase PostgreSQL | US$ 0 (free tier) |
| cron-job.org | US$ 0 |
| Domínio .fly.dev | US$ 0 |
| **TOTAL** | **US$ 0** |
