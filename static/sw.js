/**
 * BIOMA v3.7 - Service Worker para Sistema Offline
 * Diretriz 17.1: Implementação de cache e funcionalidade offline
 *
 * Estratégia de Cache:
 * - Cache-first para assets estáticos (CSS, JS, images)
 * - Network-first para APIs
 * - Fallback para páginas offline
 */

const CACHE_VERSION = 'bioma-v3.7-cache-v1';
const ASSETS_CACHE = 'bioma-assets-v1';
const API_CACHE = 'bioma-api-v1';

// Assets críticos para funcionalidade offline
const CRITICAL_ASSETS = [
    '/',
    '/static/css/correcoes-v37.css',
    '/static/js/melhorias-v37.js',
    '/static/js/app.js'
];

/**
 * Evento de instalação: cache de assets críticos
 */
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Instalando...');

    event.waitUntil(
        caches.open(ASSETS_CACHE)
            .then((cache) => {
                console.log('[Service Worker] Cacheando assets críticos...');
                return cache.addAll(CRITICAL_ASSETS);
            })
            .then(() => {
                console.log('[Service Worker] Instalação completa!');
                return self.skipWaiting(); // Ativa imediatamente
            })
            .catch((error) => {
                console.error('[Service Worker] Erro ao cachear assets:', error);
            })
    );
});

/**
 * Evento de ativação: limpar caches antigos
 */
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Ativando...');

    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        // Deletar caches antigos
                        if (cacheName !== ASSETS_CACHE && cacheName !== API_CACHE) {
                            console.log('[Service Worker] Deletando cache antigo:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('[Service Worker] Ativação completa!');
                return self.clients.claim(); // Assume controle imediatamente
            })
    );
});

/**
 * Evento de fetch: interceptar requisições e aplicar estratégias de cache
 */
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Ignorar requisições cross-origin (CDNs, APIs externas)
    if (url.origin !== location.origin) {
        return;
    }

    // Estratégia para diferentes tipos de requisição
    if (request.url.includes('/api/')) {
        // API: Network-first, fallback para cache
        event.respondWith(networkFirstStrategy(request));
    } else if (
        request.url.includes('/static/') ||
        request.url.match(/\.(css|js|png|jpg|jpeg|svg|woff|woff2|ttf)$/)
    ) {
        // Assets estáticos: Cache-first
        event.respondWith(cacheFirstStrategy(request));
    } else {
        // Páginas HTML: Network-first
        event.respondWith(networkFirstStrategy(request));
    }
});

/**
 * Estratégia Cache-First: Tenta cache primeiro, depois network
 */
async function cacheFirstStrategy(request) {
    try {
        // Tentar buscar do cache
        const cachedResponse = await caches.match(request);

        if (cachedResponse) {
            console.log('[Service Worker] Servindo do cache:', request.url);
            return cachedResponse;
        }

        // Se não estiver em cache, buscar da network
        console.log('[Service Worker] Buscando da network:', request.url);
        const networkResponse = await fetch(request);

        // Cachear a resposta para uso futuro
        if (networkResponse.ok) {
            const cache = await caches.open(ASSETS_CACHE);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.error('[Service Worker] Erro ao buscar recurso:', error);

        // Fallback para página offline
        return new Response('Offline - Recurso não disponível', {
            status: 503,
            statusText: 'Service Unavailable'
        });
    }
}

/**
 * Estratégia Network-First: Tenta network primeiro, depois cache
 */
async function networkFirstStrategy(request) {
    try {
        // Tentar buscar da network com timeout
        const networkResponse = await fetchWithTimeout(request, 5000);

        // Cachear a resposta se for API
        if (request.url.includes('/api/') && networkResponse.ok) {
            const cache = await caches.open(API_CACHE);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.warn('[Service Worker] Network falhou, tentando cache:', error);

        // Fallback para cache
        const cachedResponse = await caches.match(request);

        if (cachedResponse) {
            console.log('[Service Worker] Servindo do cache (fallback):', request.url);
            return cachedResponse;
        }

        // Se não houver cache, retornar erro
        return new Response(
            JSON.stringify({
                success: false,
                message: 'Offline - Dados não disponíveis no cache',
                offline: true
            }),
            {
                status: 503,
                statusText: 'Service Unavailable',
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}

/**
 * Fetch com timeout
 */
function fetchWithTimeout(request, timeout = 5000) {
    return Promise.race([
        fetch(request),
        new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Request timeout')), timeout)
        )
    ]);
}

/**
 * Escutar mensagens do cliente (para sync, notificações, etc.)
 */
self.addEventListener('message', (event) => {
    console.log('[Service Worker] Mensagem recebida:', event.data);

    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data.type === 'CLEAR_CACHE') {
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => caches.delete(cacheName))
                );
            })
        );
    }

    if (event.data.type === 'CACHE_STATS') {
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map(async (cacheName) => {
                        const cache = await caches.open(cacheName);
                        const keys = await cache.keys();
                        return { cacheName, count: keys.length };
                    })
                );
            }).then((stats) => {
                event.ports[0].postMessage({ type: 'CACHE_STATS_RESPONSE', stats });
            })
        );
    }
});

/**
 * Background Sync (experimental)
 */
self.addEventListener('sync', (event) => {
    console.log('[Service Worker] Background sync:', event.tag);

    if (event.tag === 'sync-data') {
        event.waitUntil(syncPendingData());
    }
});

/**
 * Sincronizar dados pendentes quando conectar
 */
async function syncPendingData() {
    console.log('[Service Worker] Sincronizando dados pendentes...');

    try {
        // Aqui você implementaria a lógica de sync com IndexedDB
        // Por exemplo, enviar dados salvos offline para o servidor

        console.log('[Service Worker] Sync completo!');
        return Promise.resolve();
    } catch (error) {
        console.error('[Service Worker] Erro ao sincronizar:', error);
        return Promise.reject(error);
    }
}

console.log('[Service Worker] Script carregado - BIOMA v3.7 Offline Mode');
