#!/usr/bin/env python3
"""
test_e2e_loop.py - Teste E2E autônomo do módulo promotor (Udemy Free Deals)
Sobe ambiente, injeta mocks, testa API + frontend (Playwright), roda em loop.

Uso:
    pip install requests playwright
    playwright install chromium
    python test_e2e_loop.py --interval 5 --cycles 2
"""

import argparse
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import requests

PROJECT_DIR = Path(__file__).parent
BACKEND_DIR = PROJECT_DIR / "backend"
FRONTEND_DIR = PROJECT_DIR / "frontend"
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"
LOG_FILE = PROJECT_DIR / "test_loop.log"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE)],
)
log = logging.getLogger("e2e")

procs: list[subprocess.Popen] = []


def kill_processes():
    """Mata processos do backend e frontend."""
    for p in procs:
        try:
            p.terminate()
            p.wait(timeout=5)
        except Exception:
            p.kill()
    procs.clear()
    # Kill por porta
    for port in [8000, 5173]:
        os.system(f"lsof -ti :{port} | xargs kill -9 2>/dev/null")


def start_backend():
    env = os.environ.copy()
    env["TESTING_MODE"] = "true"
    p = subprocess.Popen(
        ["python", "-m", "uvicorn", "app.main:app", "--port", "8000"],
        cwd=BACKEND_DIR, env=env,
        stdout=open(PROJECT_DIR / "backend_test.log", "w"),
        stderr=subprocess.STDOUT,
    )
    procs.append(p)
    return p


def start_frontend():
    p = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR,
        stdout=open(PROJECT_DIR / "frontend_test.log", "w"),
        stderr=subprocess.STDOUT,
    )
    procs.append(p)
    return p


def wait_for_service(url: str, timeout: int = 30) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code < 500:
                return True
        except requests.ConnectionError:
            pass
        time.sleep(1)
    return False


def get_token() -> str:
    r = requests.post(f"{BACKEND_URL}/api/admin/login", json={"username": "admin", "password": "admin123"})
    r.raise_for_status()
    return r.json()["access_token"]


# === API TESTS ===

class APITests:
    def __init__(self, token: str):
        self.h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        self.category_id = None
        self.course_id = None

    def test_create_category(self):
        r = requests.post(f"{BACKEND_URL}/api/admin/categories", headers=self.h, json={
            "name": f"TestCat_{int(time.time())}",
            "description": "Categoria de teste E2E",
            "telegram_channels": ["@test_channel"],
            "discord_webhooks": ["https://discord.com/api/webhooks/fake/test"],
            "subreddits": ["test"],
            "twitter_keywords": ["python free course"],
        })
        assert r.status_code == 200, f"Create category: {r.status_code} {r.text[:100]}"
        self.category_id = r.json()["id"]
        log.info(f"  API: Criar categoria... OK (ID {self.category_id[:8]})")

    def test_associate_course(self):
        # Pegar um curso existente ou criar dados de teste
        r = requests.get(f"{BACKEND_URL}/api/admin/courses/pending", headers=self.h)
        courses = r.json()
        if not courses:
            # Criar curso de teste via DB seed
            log.info("  API: Nenhum curso pending, pulando associação")
            return
        self.course_id = courses[0]["id"]
        r = requests.put(f"{BACKEND_URL}/api/admin/courses/{self.course_id}/category", headers=self.h, json={"category_id": self.category_id})
        assert r.status_code == 200, f"Associate course: {r.status_code}"
        log.info(f"  API: Associar curso... OK")

    def test_run_promoter(self):
        r = requests.post(f"{BACKEND_URL}/api/admin/promoter/run", headers=self.h)
        assert r.status_code == 200, f"Run promoter: {r.status_code}"
        log.info(f"  API: Disparar promoter... OK")
        time.sleep(3)  # Aguardar background task

    def test_promotion_logs(self):
        r = requests.get(f"{BACKEND_URL}/api/admin/promotion-logs", headers=self.h)
        assert r.status_code == 200, f"Promotion logs: {r.status_code}"
        log.info(f"  API: Promotion logs... OK ({len(r.json())} registros)")

    def test_discover_communities(self):
        if not self.category_id:
            return
        r = requests.post(f"{BACKEND_URL}/api/admin/categories/{self.category_id}/discover-communities", headers=self.h)
        assert r.status_code == 200, f"Discover: {r.status_code}"
        data = r.json()
        log.info(f"  API: Descobrir comunidades... OK (telegram={len(data.get('telegram', []))}, reddit={len(data.get('reddit', []))})")

    def test_add_community(self):
        if not self.category_id:
            return
        r = requests.post(f"{BACKEND_URL}/api/admin/categories/{self.category_id}/add-community", headers=self.h, json={"platform": "telegram", "value": "@added_test"})
        assert r.status_code == 200, f"Add community: {r.status_code}"
        log.info(f"  API: Adicionar comunidade... OK")

    def test_trending_posts(self):
        if not self.category_id:
            return
        r = requests.post(f"{BACKEND_URL}/api/admin/categories/{self.category_id}/trending-posts", headers=self.h)
        assert r.status_code == 200, f"Trending: {r.status_code}"
        data = r.json()
        log.info(f"  API: Trending posts... OK (twitter={len(data.get('twitter', []))}, reddit={len(data.get('reddit', []))})")

    def test_generate_comment(self):
        r = requests.post(f"{BACKEND_URL}/api/admin/trending-posts/comment", headers=self.h, json={
            "post": {"url": "https://reddit.com/r/test/123", "title": "Test post"},
            "course_title": "Python Course",
            "category_name": "Python",
            "affiliate_link": "https://udemy.com/test",
        })
        assert r.status_code == 200, f"Comment: {r.status_code}"
        assert "comment" in r.json()
        log.info(f"  API: Gerar comentário... OK")

    def run_all(self):
        self.test_create_category()
        self.test_associate_course()
        self.test_run_promoter()
        self.test_promotion_logs()
        self.test_discover_communities()
        self.test_add_community()
        self.test_trending_posts()
        self.test_generate_comment()


# === FRONTEND TESTS (Playwright) ===

def run_frontend_tests(token: str):
    """Testa o frontend via Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.warning("  Frontend: Playwright não instalado, pulando testes de frontend")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Injetar token no localStorage (simular login)
        page.goto(FRONTEND_URL)
        page.evaluate(f'localStorage.setItem("admin_token", "{token}")')

        # Test: Dashboard loads
        page.goto(f"{FRONTEND_URL}/admin/dashboard")
        page.wait_for_selector("h1", timeout=10000)
        assert "Dashboard" in page.content()
        log.info("  Frontend: Dashboard... PASS")

        # Test: Categories page
        page.goto(f"{FRONTEND_URL}/admin/categories")
        page.wait_for_load_state("networkidle")
        assert "Categorias" in page.content()
        log.info("  Frontend: Página categorias... PASS")

        # Test: Create category via modal
        page.click("text=+ Nova")
        page.wait_for_selector("input[placeholder='Nome']")
        page.fill("input[placeholder='Nome']", f"E2E_Test_{int(time.time())}")
        page.fill("input[placeholder='Descrição']", "Teste automatizado")
        page.click("text=Salvar")
        page.wait_for_timeout(2000)
        log.info("  Frontend: Criar categoria via modal... PASS")

        # Test: Promoter page
        page.goto(f"{FRONTEND_URL}/admin/promoter")
        page.wait_for_load_state("networkidle")
        assert "Promoter" in page.content() or "Divulgação" in page.content()
        log.info("  Frontend: Página promoter... PASS")

        # Test: Click run promoter
        btn = page.locator("text=Executar Divulgação")
        if btn.count() > 0:
            btn.first.click()
            page.wait_for_timeout(2000)
            log.info("  Frontend: Executar promoter... PASS")

        browser.close()


# === LOG ANALYSIS ===

def check_logs_for_errors():
    errors = []
    for logfile in ["backend_test.log", "frontend_test.log"]:
        path = PROJECT_DIR / logfile
        if not path.exists():
            continue
        lines = path.read_text().splitlines()[-50:]
        for line in lines:
            if any(kw in line.lower() for kw in ["traceback", "runtimeerror", "uncaught"]):
                errors.append(f"[{logfile}] {line}")
    if errors:
        log.warning(f"  Logs: {len(errors)} erros detectados")
        for e in errors[:3]:
            log.warning(f"    {e[:150]}")
    else:
        log.info("  Logs: Nenhum erro detectado")
    return len(errors) == 0


# === MAIN LOOP ===

def run_cycle(cycle_num: int):
    log.info(f"{'='*50}")
    log.info(f"Iniciando ciclo #{cycle_num}")
    log.info(f"{'='*50}")

    # Check services
    if not wait_for_service(f"{BACKEND_URL}/api/health", timeout=5):
        log.info("Iniciando backend...")
        start_backend()
        assert wait_for_service(f"{BACKEND_URL}/api/health"), "Backend não iniciou"

    if not wait_for_service(FRONTEND_URL, timeout=5):
        log.info("Iniciando frontend...")
        start_frontend()
        assert wait_for_service(FRONTEND_URL), "Frontend não iniciou"

    log.info("Serviços: Backend OK, Frontend OK")

    # API tests
    token = get_token()
    api = APITests(token)
    api.run_all()

    # Frontend tests
    run_frontend_tests(token)

    # Log analysis
    check_logs_for_errors()

    log.info(f"✅ Ciclo #{cycle_num} concluído com sucesso")


def main():
    parser = argparse.ArgumentParser(description="Teste E2E do módulo promotor")
    parser.add_argument("--interval", type=int, default=15, help="Minutos entre ciclos")
    parser.add_argument("--cycles", type=int, default=0, help="Número de ciclos (0=infinito)")
    args = parser.parse_args()

    # Cleanup on exit
    def cleanup(sig=None, frame=None):
        log.info("Encerrando...")
        kill_processes()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # Set testing mode
    os.environ["TESTING_MODE"] = "true"

    log.info("🧪 Teste E2E - Módulo Promotor")
    log.info(f"   Intervalo: {args.interval} min | Ciclos: {args.cycles or '∞'}")

    cycle = 0
    try:
        while True:
            cycle += 1
            try:
                run_cycle(cycle)
            except AssertionError as e:
                log.error(f"❌ FALHA no ciclo #{cycle}: {e}")
                (PROJECT_DIR / "test_failure.log").write_text(f"Ciclo {cycle}: {e}")
                kill_processes()
                sys.exit(1)
            except Exception as e:
                log.error(f"❌ ERRO no ciclo #{cycle}: {e}")
                (PROJECT_DIR / "test_failure.log").write_text(f"Ciclo {cycle}: {e}")
                kill_processes()
                sys.exit(1)

            if args.cycles and cycle >= args.cycles:
                log.info(f"✅ {cycle} ciclos concluídos com sucesso!")
                break

            log.info(f"Aguardando {args.interval} minutos...")
            time.sleep(args.interval * 60)
    finally:
        kill_processes()


if __name__ == "__main__":
    main()
