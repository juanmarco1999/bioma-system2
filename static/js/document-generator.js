/**
 * BIOMA v4.0 - Sistema Profissional de Geração de Documentos
 *
 * Este sistema gera documentos bonitos, modernos e impecáveis para:
 * - PDFs com layout profissional
 * - Planilhas Excel formatadas
 * - Relatórios com gráficos
 * - Documentos de alta qualidade para impressão
 *
 * @author Juan Marco (@juanmarco1999)
 * @version 4.0.0
 */

// ========== ESTILOS E CONFIGURAÇÕES ==========
const DocumentStyles = {
    // Paleta de cores do BIOMA
    colors: {
        primary: '#7C3AED',
        primaryDark: '#6D28D9',
        secondary: '#EC4899',
        accent: '#F59E0B',
        success: '#10B981',
        danger: '#EF4444',
        warning: '#F59E0B',
        info: '#3B82F6',
        textPrimary: '#1F2937',
        textSecondary: '#6B7280',
        textMuted: '#9CA3AF',
        background: '#F9FAFB',
        border: '#E5E7EB',
        white: '#FFFFFF'
    },

    // Fontes
    fonts: {
        title: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        body: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        mono: 'Consolas, "Courier New", monospace'
    },

    // Espaçamentos
    spacing: {
        page: 40,
        section: 30,
        subsection: 20,
        line: 12,
        item: 8
    },

    // Tamanhos de fonte
    fontSize: {
        h1: 24,
        h2: 20,
        h3: 16,
        h4: 14,
        body: 12,
        small: 10,
        tiny: 8
    }
};

// ========== GERADOR DE PDF PROFISSIONAL ==========
class PDFGenerator {
    constructor(options = {}) {
        this.doc = new jsPDF(options.orientation || 'portrait', 'pt', options.format || 'a4');
        this.styles = DocumentStyles;
        this.currentY = options.startY || 60;
        this.pageWidth = this.doc.internal.pageSize.getWidth();
        this.pageHeight = this.doc.internal.pageSize.getHeight();
        this.margins = {
            left: options.marginLeft || 40,
            right: options.marginRight || 40,
            top: options.marginTop || 60,
            bottom: options.marginBottom || 60
        };
        this.maxWidth = this.pageWidth - this.margins.left - this.margins.right;
    }

    // Adicionar cabeçalho com logo
    addHeader(logoBase64, title, subtitle, options = {}) {
        const { showDate = true, showPageNumbers = true } = options;

        // Logo (se fornecido)
        if (logoBase64) {
            const logoHeight = 50;
            const logoWidth = 100;
            try {
                this.doc.addImage(logoBase64, 'PNG', this.margins.left, 20, logoWidth, logoHeight);
            } catch(e) {
                console.warn('Erro ao adicionar logo:', e);
            }
        }

        // Título
        this.doc.setFontSize(this.styles.fontSize.h1);
        this.doc.setTextColor(this.styles.colors.primary);
        this.doc.setFont('helvetica', 'bold');
        this.doc.text(title, this.pageWidth / 2, 40, { align: 'center' });

        // Subtítulo
        if (subtitle) {
            this.doc.setFontSize(this.styles.fontSize.h3);
            this.doc.setTextColor(this.styles.colors.textSecondary);
            this.doc.setFont('helvetica', 'normal');
            this.doc.text(subtitle, this.pageWidth / 2, 60, { align: 'center' });
        }

        // Data
        if (showDate) {
            const dataAtual = new Date().toLocaleDateString('pt-BR', {
                day: '2-digit',
                month: 'long',
                year: 'numeric'
            });
            this.doc.setFontSize(this.styles.fontSize.small);
            this.doc.setTextColor(this.styles.colors.textMuted);
            this.doc.text(dataAtual, this.pageWidth - this.margins.right, 30, { align: 'right' });
        }

        // Linha separadora
        this.doc.setDrawColor(this.styles.colors.border);
        this.doc.setLineWidth(1);
        this.doc.line(this.margins.left, 80, this.pageWidth - this.margins.right, 80);

        this.currentY = 100;
    }

    // Adicionar seção com título
    addSection(title, content, options = {}) {
        const { color = this.styles.colors.primary, fontSize = this.styles.fontSize.h2 } = options;

        // Verificar espaço na página
        if (this.currentY + 100 > this.pageHeight - this.margins.bottom) {
            this.addPage();
        }

        // Título da seção
        this.doc.setFontSize(fontSize);
        this.doc.setTextColor(color);
        this.doc.setFont('helvetica', 'bold');
        this.doc.text(title, this.margins.left, this.currentY);

        this.currentY += this.styles.spacing.subsection;

        // Conteúdo
        if (content) {
            this.doc.setFontSize(this.styles.fontSize.body);
            this.doc.setTextColor(this.styles.colors.textPrimary);
            this.doc.setFont('helvetica', 'normal');

            const lines = this.doc.splitTextToSize(content, this.maxWidth);
            this.doc.text(lines, this.margins.left, this.currentY);
            this.currentY += lines.length * this.styles.spacing.line + this.styles.spacing.section;
        }
    }

    // Adicionar tabela formatada
    addTable(headers, rows, options = {}) {
        const {
            startY = this.currentY,
            headerColor = this.styles.colors.primary,
            altRowColor = this.styles.colors.background,
            showGridLines = true
        } = options;

        // Configuração da tabela usando autoTable
        this.doc.autoTable({
            startY: startY,
            head: [headers],
            body: rows,
            theme: 'grid',
            headStyles: {
                fillColor: headerColor,
                textColor: this.styles.colors.white,
                fontSize: this.styles.fontSize.body,
                fontStyle: 'bold',
                halign: 'center'
            },
            bodyStyles: {
                fontSize: this.styles.fontSize.small,
                textColor: this.styles.colors.textPrimary
            },
            alternateRowStyles: {
                fillColor: altRowColor
            },
            margin: { left: this.margins.left, right: this.margins.right },
            tableWidth: 'auto',
            ...options
        });

        this.currentY = this.doc.lastAutoTable.finalY + this.styles.spacing.section;
    }

    // Adicionar rodapé
    addFooter(options = {}) {
        const {
            text = 'BIOMA Uberaba v4.0 - Sistema Profissional',
            showPageNumber = true
        } = options;

        const pageCount = this.doc.internal.getNumberOfPages();

        for (let i = 1; i <= pageCount; i++) {
            this.doc.setPage(i);

            // Linha separadora
            this.doc.setDrawColor(this.styles.colors.border);
            this.doc.setLineWidth(0.5);
            this.doc.line(
                this.margins.left,
                this.pageHeight - 40,
                this.pageWidth - this.margins.right,
                this.pageHeight - 40
            );

            // Texto do rodapé
            this.doc.setFontSize(this.styles.fontSize.small);
            this.doc.setTextColor(this.styles.colors.textMuted);
            this.doc.setFont('helvetica', 'normal');
            this.doc.text(text, this.margins.left, this.pageHeight - 25);

            // Número da página
            if (showPageNumber) {
                const pageText = `Página ${i} de ${pageCount}`;
                this.doc.text(
                    pageText,
                    this.pageWidth - this.margins.right,
                    this.pageHeight - 25,
                    { align: 'right' }
                );
            }
        }
    }

    // Adicionar nova página
    addPage() {
        this.doc.addPage();
        this.currentY = this.margins.top;
    }

    // Salvar PDF
    save(filename) {
        const timestamp = new Date().toISOString().split('T')[0];
        this.doc.save(`${filename}_${timestamp}.pdf`);
    }
}

// ========== GERADOR DE EXCEL AVANÇADO ==========
class ExcelGenerator {
    constructor() {
        this.workbook = XLSX.utils.book_new();
        this.styles = DocumentStyles;
    }

    // Criar nova planilha
    addSheet(name, data, columns, options = {}) {
        const {
            freezeHeader = true,
            autoWidth = true,
            headerColor = 'FFC000',
            altRowColor = 'F2F2F2'
        } = options;

        // Preparar dados com cabeçalhos
        const headers = columns.map(col => col.label || col.key);
        const rows = data.map(row => {
            return columns.map(col => {
                let value = row[col.key];

                // Formatação especial
                if (col.format === 'currency') {
                    return typeof value === 'number' ? value : 0;
                } else if (col.format === 'date') {
                    return value ? new Date(value).toLocaleDateString('pt-BR') : '';
                } else if (col.format === 'boolean') {
                    return value ? 'Sim' : 'Não';
                }

                return value !== null && value !== undefined ? value : '';
            });
        });

        // Criar worksheet
        const ws = XLSX.utils.aoa_to_sheet([headers, ...rows]);

        // Largura das colunas
        if (autoWidth) {
            const colWidths = columns.map((col, i) => {
                const maxLength = Math.max(
                    headers[i].length,
                    ...rows.map(row => String(row[i]).length)
                );
                return { wch: Math.min(maxLength + 2, 50) };
            });
            ws['!cols'] = colWidths;
        }

        // Congelar cabeçalho
        if (freezeHeader) {
            ws['!freeze'] = { xSplit: 0, ySplit: 1 };
        }

        // Adicionar ao workbook
        XLSX.utils.book_append_sheet(this.workbook, ws, name);
    }

    // Salvar Excel
    save(filename) {
        const timestamp = new Date().toISOString().split('T')[0];
        XLSX.writeFile(this.workbook, `${filename}_${timestamp}.xlsx`);
    }
}

// ========== EXPORTAR FUNÇÕES GLOBAIS ==========
window.DocumentGenerator = {
    PDF: PDFGenerator,
    Excel: ExcelGenerator,
    styles: DocumentStyles,

    // Função helper para gerar orçamento em PDF
    generateOrcamentoPDF: function(orcamento, logo) {
        const pdf = new PDFGenerator();

        pdf.addHeader(logo, 'ORÇAMENTO', `#${orcamento.numero}`, { showDate: true });

        pdf.addSection('Dados do Cliente',
            `Nome: ${orcamento.cliente}\n` +
            `Data: ${new Date(orcamento.data).toLocaleDateString('pt-BR')}\n` +
            `Status: ${orcamento.status}`
        );

        // Tabela de serviços
        const headers = ['Descrição', 'Quantidade', 'Valor Unit.', 'Total'];
        const rows = orcamento.servicos.map(s => [
            s.nome,
            s.quantidade,
            `R$ ${s.valor.toFixed(2)}`,
            `R$ ${(s.quantidade * s.valor).toFixed(2)}`
        ]);

        pdf.addTable(headers, rows);

        // Total
        pdf.addSection('Total do Orçamento',
            `R$ ${orcamento.total.toFixed(2)}`,
            { color: DocumentStyles.colors.success, fontSize: 18 }
        );

        pdf.addFooter();
        pdf.save(`Orcamento_${orcamento.numero}`);
    },

    // Função helper para gerar relatório em Excel
    generateRelatorioExcel: function(titulo, data, columns) {
        const excel = new ExcelGenerator();
        excel.addSheet(titulo, data, columns, { freezeHeader: true, autoWidth: true });
        excel.save(titulo);
    }
};

console.log('📊 Document Generator v4.0 carregado com sucesso!');
