/**
 * BIOMA - Correções Definitivas do Sistema
 * Este arquivo corrige DEFINITIVAMENTE:
 * 1. Estoque aparecendo em todas as abas
 * 2. Carregamento infinito
 * 3. Sub-tabs não funcionando
 * 4. Abas muito grandes sem conteúdo
 */

(function() {
    'use strict';

    console.log('🔧 Carregando correções BIOMA...');

    // ========== CORREÇÃO 1: PREVENIR CARREGAMENTO INFINITO ==========

    // Flags globais para prevenir múltiplos carregamentos
    window.loadingFlags = window.loadingFlags || {};

    // Função wrapper para prevenir carregamento infinito
    window.safeLoad = function(key, loadFunction, timeout = 500) {
        if (window.loadingFlags[key]) {
            console.warn(`⚠️ Carregamento de ${key} já em andamento, ignorando...`);
            return Promise.resolve();
        }

        window.loadingFlags[key] = true;

        return new Promise((resolve, reject) => {
            setTimeout(() => {
                loadFunction()
                    .then(result => {
                        window.loadingFlags[key] = false;
                        resolve(result);
                    })
                    .catch(error => {
                        window.loadingFlags[key] = false;
                        reject(error);
                    });
            }, timeout);
        });
    };

    // ========== CORREÇÃO 2: REMOVER ESTOQUE DE ABAS INCORRETAS ==========

    // Função para remover todos os elementos de estoque de uma seção específica
    window.removeEstoqueDaSecao = function(secaoId) {
        const secao = document.getElementById(secaoId);
        if (!secao) return;

        // Remover todos os elementos relacionados a estoque
        const estoqueElements = secao.querySelectorAll(
            '[id*="estoque"], [class*="estoque"], ' +
            '[id*="Estoque"], [class*="Estoque"], ' +
            '.estoque-card, .estoque-item, #estoqueVisaoGeral, ' +
            '#estoque-resumo, #estoque-lista, #estoque-relatorio'
        );

        estoqueElements.forEach(el => {
            if (el.closest('#estoque') === null) { // Não remover se estiver dentro da seção de estoque
                console.log(`Removendo elemento de estoque indevido: ${el.id || el.className}`);
                el.remove();
            }
        });
    };

    // Executar limpeza ao carregar cada seção
    const secoesLimpar = ['dashboard', 'agendamentos', 'clientes', 'profissionais',
                          'servicos', 'produtos', 'financeiro', 'comunidade',
                          'importar', 'sistema', 'auditoria', 'configuracoes', 'avaliacoes'];

    secoesLimpar.forEach(secao => {
        const observer = new MutationObserver(() => {
            if (secao !== 'estoque' && secao !== 'produtos') {
                window.removeEstoqueDaSecao(secao);
            }
        });

        const secaoElement = document.getElementById(secao);
        if (secaoElement) {
            observer.observe(secaoElement, {
                childList: true,
                subtree: true
            });
        }
    });

    // ========== CORREÇÃO 3: CORRIGIR NAVEGAÇÃO DE SUB-TABS ==========

    window.switchSubTab = function(mainTab, subTab) {
        console.log(`Alternando sub-tab: ${mainTab} -> ${subTab}`);

        // Esconder todas as sub-tabs desta seção
        const allSubTabs = document.querySelectorAll(`#${mainTab} .sub-tab-content`);
        allSubTabs.forEach(tab => {
            tab.style.display = 'none';
        });

        // Remover classe ativa de todos os botões
        const allButtons = document.querySelectorAll(`#${mainTab} .sub-nav-btn`);
        allButtons.forEach(btn => {
            btn.classList.remove('active');
        });

        // Mostrar a sub-tab selecionada
        const selectedSubTab = document.getElementById(`${mainTab}-${subTab}`);
        if (selectedSubTab) {
            selectedSubTab.style.display = 'block';
        }

        // Adicionar classe ativa ao botão clicado
        const clickedButton = event ? event.target : null;
        if (clickedButton) {
            clickedButton.classList.add('active');
        }

        // Carregar dados da sub-tab se necessário
        const loadFunctionName = `load${capitalize(mainTab)}${capitalize(subTab)}`;
        if (typeof window[loadFunctionName] === 'function') {
            window.safeLoad(loadFunctionName, () => {
                return window[loadFunctionName]();
            });
        }
    };

    function capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    // ========== CORREÇÃO 4: CORRIGIR FUNÇÃO goTo ==========

    const originalGoTo = window.goTo;
    window.goTo = function(secao) {
        console.log(`Navegando para: ${secao}`);

        // Limpar flags de carregamento
        Object.keys(window.loadingFlags).forEach(key => {
            if (window.loadingFlags[key]) {
                console.log(`Limpando flag de carregamento: ${key}`);
                window.loadingFlags[key] = false;
            }
        });

        // Esconder todas as seções
        const allSections = document.querySelectorAll('.secao');
        allSections.forEach(section => {
            section.style.display = 'none';
        });

        // Remover classe ativa de todos os links do menu
        const allLinks = document.querySelectorAll('.sidebar a');
        allLinks.forEach(link => {
            link.classList.remove('active');
        });

        // Mostrar a seção selecionada
        const targetSection = document.getElementById(secao);
        if (targetSection) {
            targetSection.style.display = 'block';

            // Remover estoque se não for a seção de estoque ou produtos
            if (secao !== 'estoque' && secao !== 'produtos') {
                setTimeout(() => {
                    window.removeEstoqueDaSecao(secao);
                }, 100);
            }
        }

        // Adicionar classe ativa ao link clicado
        const activeLink = document.querySelector(`.sidebar a[onclick*="${secao}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }

        // Carregar dados da seção
        const loadFunctionName = `load${capitalize(secao)}`;
        if (typeof window[loadFunctionName] === 'function') {
            window.safeLoad(loadFunctionName, () => {
                return Promise.resolve(window[loadFunctionName]());
            });
        }

        // Chamar função original se existir
        if (originalGoTo && originalGoTo !== window.goTo) {
            originalGoTo(secao);
        }
    };

    // ========== CORREÇÃO 5: CORRIGIR ABAS MUITO GRANDES ==========

    // Adicionar CSS para limitar altura das abas e adicionar scroll
    const style = document.createElement('style');
    style.textContent = `
        .secao {
            max-height: calc(100vh - 120px);
            overflow-y: auto;
            overflow-x: hidden;
        }

        .sub-tab-content {
            max-height: calc(100vh - 200px);
            overflow-y: auto;
            overflow-x: hidden;
        }

        /* Estilizar scrollbar */
        .secao::-webkit-scrollbar,
        .sub-tab-content::-webkit-scrollbar {
            width: 8px;
        }

        .secao::-webkit-scrollbar-track,
        .sub-tab-content::-webkit-scrollbar-track {
            background: var(--bg-secondary, #f1f1f1);
            border-radius: 10px;
        }

        .secao::-webkit-scrollbar-thumb,
        .sub-tab-content::-webkit-scrollbar-thumb {
            background: var(--primary, #8b5cf6);
            border-radius: 10px;
        }

        .secao::-webkit-scrollbar-thumb:hover,
        .sub-tab-content::-webkit-scrollbar-thumb:hover {
            background: var(--primary-dark, #7c3aed);
        }

        /* Garantir que o conteúdo seja visível */
        .card, .dashboard-card, .stats-card {
            margin-bottom: 20px;
        }

        /* Prevenir overflow horizontal */
        * {
            box-sizing: border-box;
        }

        .table-responsive {
            overflow-x: auto;
        }
    `;
    document.head.appendChild(style);

    // ========== CORREÇÃO 6: IMPLEMENTAR FUNÇÕES DE RENDERIZAÇÃO FALTANTES ==========

    // Função genérica para renderizar tabela
    window.renderTabela = function(containerId, data, columns) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} não encontrado`);
            return;
        }

        if (!data || data.length === 0) {
            container.innerHTML = '<p style="text-align:center; padding:40px; color:#999;">Nenhum registro encontrado</p>';
            return;
        }

        let html = '<div class="table-responsive"><table class="table"><thead><tr>';

        // Cabeçalhos
        columns.forEach(col => {
            html += `<th>${col.label}</th>`;
        });
        html += '</tr></thead><tbody>';

        // Dados
        data.forEach(row => {
            html += '<tr>';
            columns.forEach(col => {
                const value = col.format ? col.format(row[col.key], row) : row[col.key];
                html += `<td>${value || '-'}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table></div>';
        container.innerHTML = html;
    };

    // Implementar funções de renderização específicas
    window.renderAgendamentosTabela = function(agendamentos, pagination) {
        window.renderTabela('agendamentos-lista', agendamentos, [
            { key: 'data', label: 'Data', format: (v) => new Date(v).toLocaleDateString('pt-BR') },
            { key: 'hora', label: 'Hora' },
            { key: 'cliente', label: 'Cliente' },
            { key: 'servico', label: 'Serviço' },
            { key: 'profissional', label: 'Profissional' },
            { key: 'status', label: 'Status' }
        ]);
    };

    window.renderServicosTabela = function(servicos, pagination) {
        window.renderTabela('servicos-lista', servicos, [
            { key: 'nome', label: 'Serviço' },
            { key: 'categoria', label: 'Categoria' },
            { key: 'duracao', label: 'Duração' },
            { key: 'preco', label: 'Preço', format: (v) => `R$ ${parseFloat(v).toFixed(2)}` },
            { key: 'status', label: 'Status' }
        ]);
    };

    window.renderProdutosTabela = function(produtos, pagination) {
        window.renderTabela('produtos-lista', produtos, [
            { key: 'nome', label: 'Produto' },
            { key: 'categoria', label: 'Categoria' },
            { key: 'estoque', label: 'Estoque' },
            { key: 'preco', label: 'Preço', format: (v) => `R$ ${parseFloat(v).toFixed(2)}` },
            { key: 'status', label: 'Status' }
        ]);
    };

    window.renderFinanceiroResumo = function(data) {
        const container = document.getElementById('financeiro-resumo');
        if (!container) return;

        const html = `
            <div class="row">
                <div class="col-md-4">
                    <div class="stats-card bg-success">
                        <h3>R$ ${(data.receitas || 0).toFixed(2)}</h3>
                        <p>Receitas</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stats-card bg-danger">
                        <h3>R$ ${(data.despesas || 0).toFixed(2)}</h3>
                        <p>Despesas</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stats-card bg-primary">
                        <h3>R$ ${((data.receitas || 0) - (data.despesas || 0)).toFixed(2)}</h3>
                        <p>Saldo</p>
                    </div>
                </div>
            </div>
        `;
        container.innerHTML = html;
    };

    window.renderResumoGeral = function(data) {
        const container = document.getElementById('dashboard-resumo');
        if (!container) return;

        const html = `
            <div class="row">
                <div class="col-md-3">
                    <div class="dashboard-card">
                        <h4>${data.agendamentos || 0}</h4>
                        <p>Agendamentos Hoje</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="dashboard-card">
                        <h4>${data.clientes || 0}</h4>
                        <p>Clientes Ativos</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="dashboard-card">
                        <h4>R$ ${(data.faturamento || 0).toFixed(2)}</h4>
                        <p>Faturamento Mensal</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="dashboard-card">
                        <h4>${data.servicos || 0}</h4>
                        <p>Serviços Realizados</p>
                    </div>
                </div>
            </div>
        `;
        container.innerHTML = html;
    };

    window.renderEstoqueVisaoGeral = function(data) {
        const container = document.getElementById('estoque-visao-geral');
        if (!container) return;

        const html = `
            <div class="row">
                <div class="col-md-4">
                    <div class="stats-card">
                        <h3>${data.totalProdutos || 0}</h3>
                        <p>Total de Produtos</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stats-card bg-warning">
                        <h3>${data.produtosEmFalta || 0}</h3>
                        <p>Produtos em Falta</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stats-card bg-success">
                        <h3>R$ ${(data.valorTotal || 0).toFixed(2)}</h3>
                        <p>Valor Total em Estoque</p>
                    </div>
                </div>
            </div>
        `;
        container.innerHTML = html;
    };

    // ========== INICIALIZAÇÃO ==========

    // Executar correções quando o DOM estiver pronto
    function init() {
        console.log('✅ Correções BIOMA aplicadas com sucesso!');

        // Limpar estoque de seções incorretas
        secoesLimpar.forEach(secao => {
            if (secao !== 'estoque' && secao !== 'produtos') {
                window.removeEstoqueDaSecao(secao);
            }
        });

        // Adicionar evento de limpeza ao mudar de seção
        document.addEventListener('click', function(e) {
            const link = e.target.closest('a[onclick*="goTo"]');
            if (link) {
                const secao = link.getAttribute('onclick').match(/goTo\('(\w+)'\)/)?.[1];
                if (secao && secao !== 'estoque' && secao !== 'produtos') {
                    setTimeout(() => {
                        window.removeEstoqueDaSecao(secao);
                    }, 200);
                }
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();