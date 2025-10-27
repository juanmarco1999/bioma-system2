/**
 * BIOMA v4.0 - Offline Manager
 * Sistema completo de gerenciamento offline com IndexedDB
 *
 * Funcionalidades:
 * - IndexedDB para armazenamento local
 * - Fila de operações pendentes
 * - Sincronização automática
 * - Detector de conectividade
 * - Indicadores visuais de status
 */

// ============================================================================
// INDEXEDDB MANAGER
// ============================================================================

class OfflineDB {
    constructor() {
        this.dbName = 'BIOMA_Offline';
        this.version = 1;
        this.db = null;
    }

    /**
     * Inicializar IndexedDB
     */
    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.version);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                console.log('✅ IndexedDB inicializado');
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Store para operações pendentes
                if (!db.objectStoreNames.contains('pendingOperations')) {
                    const pendingStore = db.createObjectStore('pendingOperations', {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    pendingStore.createIndex('timestamp', 'timestamp', { unique: false });
                    pendingStore.createIndex('type', 'type', { unique: false });
                }

                // Store para dados em cache
                if (!db.objectStoreNames.contains('cachedData')) {
                    const cacheStore = db.createObjectStore('cachedData', {
                        keyPath: 'key'
                    });
                    cacheStore.createIndex('expiry', 'expiry', { unique: false });
                }

                console.log('📦 Stores IndexedDB criados');
            };
        });
    }

    /**
     * Adicionar operação pendente
     */
    async addPendingOperation(operation) {
        const tx = this.db.transaction(['pendingOperations'], 'readwrite');
        const store = tx.objectStore('pendingOperations');

        const data = {
            ...operation,
            timestamp: Date.now(),
            status: 'pending'
        };

        return new Promise((resolve, reject) => {
            const request = store.add(data);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Obter todas as operações pendentes
     */
    async getPendingOperations() {
        const tx = this.db.transaction(['pendingOperations'], 'readonly');
        const store = tx.objectStore('pendingOperations');

        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Remover operação pendente
     */
    async removePendingOperation(id) {
        const tx = this.db.transaction(['pendingOperations'], 'readwrite');
        const store = tx.objectStore('pendingOperations');

        return new Promise((resolve, reject) => {
            const request = store.delete(id);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Salvar dados em cache
     */
    async setCachedData(key, value, expiryMinutes = 60) {
        const tx = this.db.transaction(['cachedData'], 'readwrite');
        const store = tx.objectStore('cachedData');

        const data = {
            key,
            value,
            expiry: Date.now() + (expiryMinutes * 60 * 1000),
            savedAt: Date.now()
        };

        return new Promise((resolve, reject) => {
            const request = store.put(data);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Obter dados do cache
     */
    async getCachedData(key) {
        const tx = this.db.transaction(['cachedData'], 'readonly');
        const store = tx.objectStore('cachedData');

        return new Promise((resolve, reject) => {
            const request = store.get(key);
            request.onsuccess = () => {
                const data = request.result;

                // Verificar se expirou
                if (data && data.expiry > Date.now()) {
                    resolve(data.value);
                } else {
                    resolve(null);
                }
            };
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Limpar dados expirados
     */
    async cleanExpiredData() {
        const tx = this.db.transaction(['cachedData'], 'readwrite');
        const store = tx.objectStore('cachedData');
        const index = store.index('expiry');

        const range = IDBKeyRange.upperBound(Date.now());

        return new Promise((resolve, reject) => {
            const request = index.openCursor(range);
            let deletedCount = 0;

            request.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    cursor.delete();
                    deletedCount++;
                    cursor.continue();
                } else {
                    console.log(`🧹 ${deletedCount} registros expirados removidos`);
                    resolve(deletedCount);
                }
            };
            request.onerror = () => reject(request.error);
        });
    }
}

// ============================================================================
// CONNECTIVITY DETECTOR
// ============================================================================

class ConnectivityDetector {
    constructor() {
        this.online = navigator.onLine;
        this.listeners = [];
    }

    /**
     * Inicializar detector
     */
    init() {
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());

        // Verificar conectividade real (não só navigator.onLine)
        setInterval(() => this.checkRealConnectivity(), 30000); // A cada 30s

        console.log('🌐 Detector de conectividade iniciado');
        this.updateUI();
    }

    /**
     * Verificar conectividade real fazendo ping ao servidor
     */
    async checkRealConnectivity() {
        try {
            const response = await fetch('/api/ping', {
                method: 'GET',
                cache: 'no-cache',
                timeout: 5000
            });

            const wasOnline = this.online;
            this.online = response.ok;

            if (wasOnline !== this.online) {
                this.online ? this.handleOnline() : this.handleOffline();
            }
        } catch (error) {
            if (this.online) {
                this.online = false;
                this.handleOffline();
            }
        }
    }

    /**
     * Handler quando volta online
     */
    handleOnline() {
        console.log('✅ Sistema ONLINE');
        this.online = true;
        this.updateUI();
        this.notifyListeners('online');

        // Tentar sincronizar dados pendentes
        if (window.offlineSync) {
            window.offlineSync.syncPendingOperations();
        }
    }

    /**
     * Handler quando fica offline
     */
    handleOffline() {
        console.log('⚠️ Sistema OFFLINE');
        this.online = false;
        this.updateUI();
        this.notifyListeners('offline');
    }

    /**
     * Atualizar UI com status de conectividade
     */
    updateUI() {
        const indicator = document.getElementById('connectivity-indicator');
        if (!indicator) return;

        if (this.online) {
            indicator.className = 'connectivity-indicator online';
            indicator.innerHTML = '<i class="bi bi-wifi"></i> Online';
            indicator.title = 'Conectado ao servidor';
        } else {
            indicator.className = 'connectivity-indicator offline';
            indicator.innerHTML = '<i class="bi bi-wifi-off"></i> Offline';
            indicator.title = 'Sem conexão - Modo offline ativo';
        }
    }

    /**
     * Adicionar listener de mudança de status
     */
    addListener(callback) {
        this.listeners.push(callback);
    }

    /**
     * Notificar listeners
     */
    notifyListeners(status) {
        this.listeners.forEach(callback => callback(status));
    }

    /**
     * Verificar se está online
     */
    isOnline() {
        return this.online;
    }
}

// ============================================================================
// SYNC MANAGER
// ============================================================================

class SyncManager {
    constructor(offlineDB, connectivityDetector) {
        this.db = offlineDB;
        this.connectivity = connectivityDetector;
        this.syncing = false;
    }

    /**
     * Sincronizar operações pendentes
     */
    async syncPendingOperations() {
        if (this.syncing || !this.connectivity.isOnline()) {
            return;
        }

        this.syncing = true;
        console.log('🔄 Iniciando sincronização...');

        try {
            const operations = await this.db.getPendingOperations();

            if (operations.length === 0) {
                console.log('✅ Nenhuma operação pendente');
                this.syncing = false;
                return;
            }

            console.log(`📤 Sincronizando ${operations.length} operações...`);

            let successCount = 0;
            let errorCount = 0;

            for (const operation of operations) {
                try {
                    await this.executeOperation(operation);
                    await this.db.removePendingOperation(operation.id);
                    successCount++;
                } catch (error) {
                    console.error(`❌ Erro ao sincronizar operação ${operation.id}:`, error);
                    errorCount++;
                }
            }

            console.log(`✅ Sincronização completa: ${successCount} sucesso, ${errorCount} erros`);

            // Notificar usuário
            if (successCount > 0 && window.Swal) {
                Swal.fire({
                    icon: 'success',
                    title: 'Sincronização Completa',
                    text: `${successCount} operação(ões) sincronizada(s) com sucesso`,
                    timer: 3000,
                    showConfirmButton: false
                });
            }

        } catch (error) {
            console.error('❌ Erro na sincronização:', error);
        } finally {
            this.syncing = false;
        }
    }

    /**
     * Executar operação pendente
     */
    async executeOperation(operation) {
        const { type, endpoint, method, data } = operation;

        console.log(`📤 Executando: ${method} ${endpoint}`);

        const response = await fetch(endpoint, {
            method: method || 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: data ? JSON.stringify(data) : undefined
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
    }
}

// ============================================================================
// INICIALIZAÇÃO GLOBAL
// ============================================================================

window.offlineDB = new OfflineDB();
window.connectivityDetector = new ConnectivityDetector();

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Inicializar IndexedDB
        await window.offlineDB.init();

        // Limpar dados expirados
        await window.offlineDB.cleanExpiredData();

        // Inicializar detector de conectividade
        window.connectivityDetector.init();

        // Inicializar sync manager
        window.offlineSync = new SyncManager(
            window.offlineDB,
            window.connectivityDetector
        );

        // Adicionar listener para sincronizar quando voltar online
        window.connectivityDetector.addListener((status) => {
            if (status === 'online' && window.offlineSync) {
                setTimeout(() => {
                    window.offlineSync.syncPendingOperations();
                }, 2000); // Aguardar 2s antes de sincronizar
            }
        });

        console.log('✅ Sistema Offline Manager inicializado');

    } catch (error) {
        console.error('❌ Erro ao inicializar Offline Manager:', error);
    }
});

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Salvar operação offline para sincronizar depois
 */
async function saveOfflineOperation(type, endpoint, method, data) {
    if (!window.offlineDB || !window.offlineDB.db) {
        console.warn('⚠️ IndexedDB não inicializado');
        return;
    }

    try {
        const id = await window.offlineDB.addPendingOperation({
            type,
            endpoint,
            method,
            data
        });

        console.log(`💾 Operação salva offline (ID: ${id})`);

        // Notificar usuário
        if (window.Swal) {
            Swal.fire({
                icon: 'info',
                title: 'Operação Salva',
                text: 'Sua ação foi salva e será sincronizada quando você estiver online',
                timer: 3000,
                showConfirmButton: false
            });
        }

        return id;
    } catch (error) {
        console.error('❌ Erro ao salvar operação offline:', error);
        throw error;
    }
}

/**
 * Obter estatísticas do sistema offline
 */
async function getOfflineStats() {
    if (!window.offlineDB || !window.offlineDB.db) {
        return null;
    }

    const pending = await window.offlineDB.getPendingOperations();

    return {
        pendingCount: pending.length,
        isOnline: window.connectivityDetector?.isOnline() || false,
        dbReady: true
    };
}

// Exportar para uso global
window.saveOfflineOperation = saveOfflineOperation;
window.getOfflineStats = getOfflineStats;

console.log('📦 Offline Manager carregado');
