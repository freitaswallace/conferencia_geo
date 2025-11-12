# Verificador de Georreferenciamento V3.0

## 🎯 Nova Abordagem: Extração para Excel + Comparação Estruturada

### 📋 Resumo das Mudanças

A **Versão 3.0** implementa duas mudanças estratégicas fundamentais:

1. **Foco exclusivo: INCRA vs. PROJETO** (Memorial Descritivo removido)
2. **Nova abordagem de extração:** PDF → Excel → Comparação

**ANTES (V1/V2):**
```
PDF → OCR em tempo real (Gemini) → Comparação
Documentos: INCRA + Memorial + Projeto
```

**AGORA (V3):**
```
PDF → Extração para Excel (Gemini) → Comparação de dados estruturados
Documentos: INCRA + PROJETO apenas
```

### ✅ Benefícios da Nova Abordagem

1. **Elimina erros de OCR em tempo real**: Os dados são extraídos uma única vez com validação
2. **Dados auditáveis**: Excel files ficam salvos para revisão manual
3. **Comparação precisa**: Trabalha com dados estruturados, não imagens
4. **Rastreabilidade**: Arquivos intermediários disponíveis para conferência

### 🔧 Componentes Integrados

#### Arquivos Base
- `process_memorial_descritivo_v2.py`: Funções de extração usando Gemini API
- `gui_memorial_descritivo_v2.py`: Interface gráfica para extração standalone

#### Novo Script Principal
- `verificador_georreferenciamento_v3.py`: Integração completa

### 📊 Fluxo de Trabalho V3

#### Etapa 1: Extração INCRA
```python
incra_excel, incra_data = _extrair_pdf_para_excel(incra_pdf, tipo="incra")
```
- Usa extração especializada para formato INCRA
- Gera arquivo Excel temporário
- Retorna dados estruturados em JSON

#### Etapa 2: Extração Memorial/Projeto
```python
memorial_excel, memorial_data = _extrair_pdf_para_excel(memorial_pdf, tipo="normal")
```
- Extração genérica para memoriais de projeto
- Gera arquivo Excel temporário
- Retorna dados estruturados em JSON

#### Etapa 3: Comparação Estruturada
```python
relatorio = _construir_relatorio_comparacao(incluir_projeto, incluir_memorial)
```
- Compara dados linha por linha
- Identifica diferenças com precisão
- Gera relatório HTML formatado

### 🆕 Novas Funções

#### `_extrair_pdf_para_excel(pdf_path, tipo)`
Extrai tabela de PDF para Excel usando Gemini API

**Parâmetros:**
- `pdf_path`: Caminho do PDF
- `tipo`: "incra" ou "normal"

**Retorna:**
- Tupla `(excel_path, dados_dict)`

#### `_ler_dados_excel(excel_path)`
Lê dados estruturados de Excel gerado

**Retorna:**
- Dicionário com estrutura padronizada

#### `_construir_relatorio_comparacao(incluir_projeto, incluir_memorial)`
Compara dados estruturados e gera relatório HTML

**Retorna:**
- String com HTML/Markdown do relatório

### 📁 Estrutura de Dados

```python
{
  "header_row1": ["VÉRTICE", "SEGMENTO VANTE"],
  "header_row2": ["Código", "Longitude", "Latitude", "Altitude (m)",
                  "Código", "Azimute", "Dist. (m)", "Confrontações"],
  "data": [
    ["AKE-V-0166", "-48°34'14,782\"", "-20°50'45,291\"", "532,78",
     "AKE-M-1028", "140°40'", "43,85", "CNS: 12.102-0"],
    ...
  ]
}
```

### 🚀 Como Usar

1. **Execute o script V3:**
   ```bash
   python3 verificador_georreferenciamento_v3.py
   ```

2. **Interface idêntica à V2:**
   - Informe API Key do Gemini
   - Selecione PDFs (INCRA, Memorial, Projeto)
   - Clique em "Comparar"

3. **Novo fluxo interno:**
   - [1/3] Extraindo INCRA para Excel...
   - [2/3] Extraindo Memorial para Excel...
   - [3/3] Comparando dados estruturados...
   - ✅ Relatório gerado!

4. **Arquivos gerados:**
   - `/tmp/conferencia_geo/incra_extraido.xlsx`
   - `/tmp/conferencia_geo/memorial_extraido.xlsx`
   - `/tmp/conferencia_geo/projeto_extraido.xlsx`

### 📦 Dependências

```bash
pip install pdf2image Pillow google-generativeai openpyxl python-docx
```

**Nota:** Requer `poppler-utils` instalado no sistema.

### 🔄 Compatibilidade

- ✅ Interface GUI mantida 100% compatível
- ✅ Mesmos arquivos de entrada (PDFs)
- ✅ Mesmo formato de saída (HTML)
- ✅ Funcionalidade de comparação visual manual preservada

### 📈 Melhorias Futuras

- [ ] Cache de extrações para evitar reprocessamento
- [ ] Comparação com tolerância para diferenças mínimas
- [ ] Exportação direta para Excel comparativo
- [ ] Integração com banco de dados para histórico

### 🐛 Troubleshooting

**Erro: "Module process_memorial_descritivo_v2 not found"**
- Certifique-se de que os arquivos estão no mesmo diretório

**Erro: "API key inválida"**
- Verifique a API Key do Gemini em https://makersuite.google.com/app/apikey

**Excel não encontrado após extração**
- Verifique permissões em `/tmp/conferencia_geo/`

### 📝 Changelog

**V3.0 (2025-11-12)**
- ✨ Nova abordagem: Extração para Excel primeiro
- ✨ Integração com process_memorial_descritivo_v2.py
- ✨ Comparação de dados estruturados
- ✨ Arquivos Excel auditáveis
- 🔧 Eliminação de erros de OCR em tempo real

**V2.0**
- 🔧 OCR célula por célula com validação cruzada
- 🔧 Estratégia em duas etapas para códigos
- 🔧 Correções de sequência e coordenadas

**V1.0**
- 🎉 Versão inicial com OCR direto

---

**Autor**: Sistema Automatizado
**Data**: 2025-11-12
**Branch**: claude/refactor-incra-project-tables-011CV4CmMcB9Sey8p7oEPT2x
