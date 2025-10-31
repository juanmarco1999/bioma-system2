"""
Configuração otimizada do Gunicorn para BIOMA v4.0
Previne worker timeout e otimiza uso de memória
"""

import multiprocessing
import os

# Bind
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"

# Workers
# Recomendação: 2-4 workers para 512MB RAM
workers = int(os.getenv('GUNICORN_WORKERS', '2'))

# Threads por worker (aumenta throughput sem usar muita RAM)
threads = int(os.getenv('GUNICORN_THREADS', '4'))

# Timeouts
timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))  # 2 minutos (vs 30s default)
graceful_timeout = int(os.getenv('GUNICORN_GRACEFUL_TIMEOUT', '60'))  # 1 minuto
keepalive = int(os.getenv('GUNICORN_KEEPALIVE', '5'))

# Worker class
worker_class = 'sync'  # ou 'gthread' para melhor concorrência

# Reciclar workers após N requisições (previne memory leaks)
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', '1000'))
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', '50'))

# Worker temp directory (usar shared memory para melhor performance)
worker_tmp_dir = '/dev/shm' if os.path.exists('/dev/shm') else None

# Preload app (economiza memória, mas dificulta reload)
preload_app = True

# Logging
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
accesslog = '-'  # stdout
errorlog = '-'   # stdout
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Server hooks
def on_starting(server):
    """Hook executado quando o servidor inicia"""
    print("🚀 BIOMA v4.0 - Gunicorn Starting")
    print(f"   Workers: {workers}")
    print(f"   Threads: {threads}")
    print(f"   Timeout: {timeout}s")
    print(f"   Max Requests: {max_requests}")

def on_reload(server):
    """Hook executado quando há reload"""
    print("🔄 Gunicorn Reload")

def when_ready(server):
    """Hook executado quando o servidor está pronto"""
    print("✅ Gunicorn Ready - Server listening")

def worker_int(worker):
    """Hook executado quando worker recebe SIGINT"""
    print(f"⚠️  Worker {worker.pid} received SIGINT")

def worker_abort(worker):
    """Hook executado quando worker é abortado"""
    print(f"❌ Worker {worker.pid} ABORTED (timeout?)")

def post_fork(server, worker):
    """Hook executado após fork do worker"""
    print(f"👶 Worker {worker.pid} spawned")

def post_worker_init(worker):
    """Hook executado após inicialização do worker"""
    print(f"✅ Worker {worker.pid} initialized")

def worker_exit(server, worker):
    """Hook executado quando worker sai"""
    print(f"👋 Worker {worker.pid} exiting")
