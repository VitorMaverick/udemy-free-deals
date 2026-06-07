#!/bin/bash
set -e

APP="udemy-free-deals"

echo "🚀 Deploy Gratuito - Udemy Free Deals"
echo "======================================"
echo "Stack: Fly.io (US\$0) + Supabase (US\$0)"
echo ""

# Verificações
if ! command -v fly &> /dev/null; then
    echo "❌ flyctl não encontrado."
    echo "   Instale: curl -L https://fly.io/install.sh | sh"
    exit 1
fi

fly auth whoami > /dev/null 2>&1 || { echo "❌ Faça login: fly auth login"; exit 1; }
echo "✅ Autenticado no Fly.io"

# Criar app
if ! fly apps list 2>/dev/null | grep -q "$APP"; then
    echo "📦 Criando app '$APP'..."
    fly apps create "$APP"
else
    echo "✅ App '$APP' já existe"
fi

# Secrets
echo ""
echo "🔐 Configurando secrets..."
echo "   (Deixe vazio para pular se já estiverem configurados)"
echo ""
read -p "DATABASE_URL do Supabase (postgresql+asyncpg://...): " DB_URL

if [ -n "$DB_URL" ]; then
    read -p "SECRET_KEY (Enter para gerar): " SECRET
    SECRET=${SECRET:-$(openssl rand -hex 32)}
    read -p "ADMIN_USERNAME [admin]: " ADMIN_USER
    ADMIN_USER=${ADMIN_USER:-admin}
    read -sp "ADMIN_PASSWORD: " ADMIN_PASS
    echo ""

    fly secrets set \
        DATABASE_URL="$DB_URL" \
        SECRET_KEY="$SECRET" \
        ADMIN_USERNAME="$ADMIN_USER" \
        ADMIN_PASSWORD="$ADMIN_PASS" \
        --app "$APP"
    echo "✅ Secrets configurados"
else
    echo "⏭️  Secrets pulados (já configurados)"
fi

# Deploy
echo ""
echo "🚀 Fazendo deploy..."
fly deploy --app "$APP"

echo ""
echo "======================================"
echo "✅ Deploy concluído!"
echo ""
echo "🌐 Site: https://${APP}.fly.dev"
echo "🔑 Admin: https://${APP}.fly.dev/admin"
echo "📋 Logs: fly logs --app $APP"
echo "💰 Custo: fly billing view"
echo "======================================"
