#!/bin/bash
# monitor.sh - Script de monitoramento autônomo para Udemy Free Deals
# Roda em loop: verifica serviços, executa crawler, analisa logs

PROJECT_DIR="/home/vitor.maverick/repo/udemy-free-deals"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOG_DIR="$PROJECT_DIR/logs"
CRAWLER_INTERVAL=1800  # 30 minutos em segundos
BACKEND_PORT=8000
FRONTEND_PORT=5173

mkdir -p "$LOG_DIR"

# Arquivos de log
MONITOR_LOG="$LOG_DIR/monitor.log"
ERRORS_LOG="$LOG_DIR/errors.log"
CRAWLER_LOG="$LOG_DIR/crawler_alerts.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$MONITOR_LOG"; }
log_error() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$ERRORS_LOG" "$MONITOR_LOG"; }
log_crawler() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$CRAWLER_LOG" "$MONITOR_LOG"; }

get_token() {
    curl -s -X POST "http://localhost:$BACKEND_PORT/api/admin/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null
}

check_backend() {
    curl -sf "http://localhost:$BACKEND_PORT/api/health" > /dev/null 2>&1
}

check_frontend() {
    curl -sf "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1
}

start_backend() {
    log "Iniciando backend..."
    cd "$BACKEND_DIR" && source venv/bin/activate
    nohup uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT > "$LOG_DIR/backend.log" 2>&1 &
    echo $! > "$LOG_DIR/backend.pid"
    sleep 3
    if check_backend; then
        log "✅ Backend iniciado (PID $(cat $LOG_DIR/backend.pid))"
    else
        log_error "Backend falhou ao iniciar"
        return 1
    fi
}

start_frontend() {
    log "Iniciando frontend..."
    cd "$FRONTEND_DIR"
    nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
    echo $! > "$LOG_DIR/frontend.pid"
    sleep 4
    if check_frontend; then
        log "✅ Frontend iniciado (PID $(cat $LOG_DIR/frontend.pid))"
    else
        log_error "Frontend falhou ao iniciar"
        return 1
    fi
}

restart_backend() {
    log "⚠️ Reiniciando backend..."
    [ -f "$LOG_DIR/backend.pid" ] && kill $(cat "$LOG_DIR/backend.pid") 2>/dev/null
    pkill -f "uvicorn app.main" 2>/dev/null
    sleep 2
    start_backend
}

restart_frontend() {
    log "⚠️ Reiniciando frontend..."
    [ -f "$LOG_DIR/frontend.pid" ] && kill $(cat "$LOG_DIR/frontend.pid") 2>/dev/null
    sleep 2
    start_frontend
}

check_logs_for_errors() {
    if [ -f "$LOG_DIR/backend.log" ]; then
        ERRORS=$(tail -50 "$LOG_DIR/backend.log" | grep -ciE "error|traceback|exception|500" 2>/dev/null || echo 0)
        if [ "$ERRORS" -gt 0 ]; then
            LAST_ERROR=$(tail -50 "$LOG_DIR/backend.log" | grep -iE "error|traceback|exception|500" | tail -1)
            log_error "Backend log: $LAST_ERROR"
        fi
    fi
}

run_crawler() {
    log "🔄 EXECUTANDO CRAWLER..."
    TOKEN=$(get_token)
    if [ -z "$TOKEN" ]; then
        log_error "Não foi possível obter token JWT"
        return 1
    fi

    RESPONSE=$(curl -s -X POST "http://localhost:$BACKEND_PORT/api/admin/crawler/run" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json")
    log "Crawler disparado: $RESPONSE"

    # Aguardar crawler finalizar (roda em background no server)
    log "Aguardando crawler (60s)..."
    sleep 60

    # Verificar resultados
    PENDING=$(curl -s "http://localhost:$BACKEND_PORT/api/admin/courses/pending" \
        -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json;print(len(json.load(sys.stdin)))" 2>/dev/null)

    LOGS=$(curl -s "http://localhost:$BACKEND_PORT/api/admin/logs?limit=5" \
        -H "Authorization: Bearer $TOKEN")
    LAST_LOG=$(echo "$LOGS" | python3 -c "import sys,json;data=json.load(sys.stdin);print(data[0]['message'] if data else 'sem logs')" 2>/dev/null)

    log "📊 Último log crawler: $LAST_LOG"
    log "📊 Cursos pendentes: ${PENDING:-0}"

    if [ "${PENDING:-0}" = "0" ]; then
        log_crawler "⚠️ ALERTA: Nenhuma nova oferta encontrada no último ciclo."
    else
        log_crawler "✅ Crawler OK: $PENDING cursos pendentes no sistema"
    fi
}

check_post_today() {
    TOKEN=$(get_token)
    TODAY=$(date '+%Y-%m-%d')
    POST=$(curl -s "http://localhost:$BACKEND_PORT/api/posts/$TODAY" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('slug',''))" 2>/dev/null)
    
    if [ "$POST" = "$TODAY" ]; then
        log "📰 Post do dia existe: $TODAY"
    else
        # Verificar se há cursos prontos para publicar
        READY=$(curl -s "http://localhost:$BACKEND_PORT/api/admin/courses/ready" \
            -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json;print(len(json.load(sys.stdin)))" 2>/dev/null)
        if [ "${READY:-0}" -gt 0 ]; then
            log "📰 Sem post do dia, mas $READY cursos prontos. Considere publicar."
        fi
    fi
}

status_report() {
    BACKEND_STATUS="❌ DOWN"
    FRONTEND_STATUS="❌ DOWN"
    check_backend && BACKEND_STATUS="✅ OK (PID $(cat $LOG_DIR/backend.pid 2>/dev/null || echo '?'))"
    check_frontend && FRONTEND_STATUS="✅ OK (PID $(cat $LOG_DIR/frontend.pid 2>/dev/null || echo '?'))"
    log "STATUS: Backend $BACKEND_STATUS | Frontend $FRONTEND_STATUS"
}

# === MAIN LOOP ===
log "=========================================="
log "🚀 MONITOR INICIADO - Udemy Free Deals"
log "=========================================="

# Setup inicial
check_backend || start_backend
check_frontend || start_frontend

LAST_CRAWLER_RUN=0

while true; do
    # 1. Status
    status_report

    # 2. Verificar se serviços estão UP, reiniciar se necessário
    if ! check_backend; then
        log_error "Backend caiu!"
        restart_backend
    fi
    if ! check_frontend; then
        log_error "Frontend caiu!"
        restart_frontend
    fi

    # 3. Analisar logs por erros
    check_logs_for_errors

    # 4. Crawler a cada CRAWLER_INTERVAL
    NOW=$(date +%s)
    ELAPSED=$((NOW - LAST_CRAWLER_RUN))
    if [ $ELAPSED -ge $CRAWLER_INTERVAL ]; then
        run_crawler
        check_post_today
        LAST_CRAWLER_RUN=$NOW
    fi

    # 5. Aguardar antes do próximo check (60s)
    sleep 60
done
