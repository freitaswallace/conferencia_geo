# 🏛️ Verificador de Georreferenciamento INCRA v4.0

## 🎯 Novidades da Versão 4.0

### Interface Moderna e Profissional
- **Design limpo** com tema clam e cores modernas (azul #2196F3)
- **Fonte Segoe UI** para melhor legibilidade
- **Layout organizado** com cabeçalhos e seções bem definidas
- **Gradientes** e efeitos visuais profissionais

### 🔑 Gerenciamento de API Key
- **Salvamento permanente** da API Key do Gemini
- **Configuração única**: não precisa inserir a chave a cada uso
- **Armazenamento seguro** em `~/.conferencia_geo/config.ini`
- **Indicador visual** de status da API Key configurada

### 📋 Número de Prenotação
- **Campo obrigatório** para todas as operações
- **Validação automática**: aceita apenas números
- **Salvamento automático** do relatório com nomenclatura baseada no número
- **Formato do relatório**: `Relatório_INCRA_[numero].html`

### 💾 Salvamento Automático
- **Sem botão "Salvar"**: processo totalmente automático
- **Local fixo**: `C:\Users\[Usuario]\Documentos\Relatórios INCRA\`
- **Criação automática** da pasta se não existir
- **Abertura automática** no navegador após geração

---

## 🤖 MODO AUTOMÁTICO - Principal Novidade!

### Fluxo Completo Automatizado

#### 1️⃣ **Busca Automática de Arquivo TIFF**
- Busca na rede: `\\192.168.20.100\trabalho\TRABALHO\IMAGENS\IMOVEIS\DOCUMENTOS - DIVERSOS`
- **Lógica de subpasta**: `ceil(numero / 1000) * 1000` formatado com 8 dígitos
- **Exemplo**:
  - Prenotação: `229885`
  - Subpasta: `00230000`
  - Arquivo: `00229885.tif`
  - Caminho completo: `\\...\00230000\00229885.tif`

#### 2️⃣ **Conversão TIFF → PDF**
- **Cópia** para `Downloads\conferencia_geo_temp\`
- **Conversão multi-página** usando Pillow (PIL)
- **Resolução**: 200 DPI para qualidade ótima

#### 3️⃣ **Extração Inteligente com IA**
Usa **Google Gemini AI** para identificar e extrair automaticamente:

**Memorial INCRA:**
- Busca por textos: "MINISTÉRIO DA AGRICULTURA", "INCRA", "MEMORIAL DESCRITIVO"
- Identifica tabela com: "VÉRTICE", "SEGMENTO VANTE", "Confrontações"
- Extrai apenas as páginas relevantes

**Planta/Projeto:**
- Busca por: "PLANTA DO IMÓVEL GEORREFERENCIADO", "PLANTA DE SITUAÇÃO"
- Identifica: "Código INCRA:", "Matrícula nº:", "Responsável técnico:"
- Detecta tabela de coordenadas e mapas com vértices

#### 4️⃣ **Sistema de Backup Automático**
Salva cópias dos PDFs extraídos:
- **INCRA**: `Documentos\Relatórios INCRA\PDF_INCRAS\INCRA_[numero]_[timestamp].pdf`
- **PROJETO**: `Documentos\Relatórios INCRA\PDF_PLANTAS\PROJETO_[numero]_[timestamp].pdf`

#### 5️⃣ **Preview e Confirmação**
- **Thumbnails** da primeira página de cada documento
- **Botões de decisão**:
  - ✅ **CONTINUAR**: Documentos corretos → prossegue com comparação
  - ✋ **FAZER MANUAL**: Documentos incorretos → alterna para modo manual

---

## 📝 MODO MANUAL

### Interface Tradicional
- **Seleção manual** dos arquivos PDF
- **Botão único**: "🔍 COMPARAR DOCUMENTOS"
- **Validação**: garante que todos os campos estão preenchidos

### Uso
1. Selecione o PDF do **Memorial INCRA**
2. Selecione o PDF da **Planta/Projeto**
3. Insira o **Número de Prenotação**
4. Clique em **COMPARAR DOCUMENTOS**

---

## 📊 Relatório HTML Profissional

### Características
- **Design moderno** com gradientes e cards
- **Tabelas responsivas** com hover effects
- **Cores intuitivas**:
  - 🟢 Verde: Campos idênticos
  - 🔴 Vermelho: Campos diferentes
- **Duas seções separadas**:
  1. **VÉRTICE**: Código, Longitude, Latitude, Altitude
  2. **SEGMENTO VANTE**: Código, Azimute, Distância
- **Resumo estatístico** completo
- **Informações do cabeçalho**: Data, hora, número de prenotação

### Normalização de Dados
O sistema aplica automaticamente:
- ✅ Remoção de espaços em branco extras
- ✅ Conversão de **pontos para vírgulas** (padrão brasileiro)
- ✅ Normalização de **caracteres Unicode** (′ → ', ″ → ")
- ✅ Remoção de prefixos/sufixos de coordenadas (-, W, S)
- ✅ Comparação inteligente ignorando diferenças de formato

---

## 🛠️ Instalação e Dependências

### Requisitos do Sistema
```bash
# Bibliotecas Python
pip install pdf2image Pillow google-generativeai openpyxl PyPDF2

# Ferramenta externa (necessária)
# Ubuntu/Debian:
sudo apt-get install poppler-utils

# macOS:
brew install poppler

# Windows: baixar poppler e adicionar ao PATH
```

### Arquivos Necessários
- `verificador_georreferenciamento_v4.py` (principal)
- `process_memorial_descritivo_v2.py` (funções auxiliares)

---

## 🚀 Como Usar

### Primeira Execução
1. **Configure a API Key**:
   - Clique em "⚙️ Configurar API Key"
   - Insira sua chave do Google Gemini
   - Clique em "💾 Salvar"
   - ✅ A chave fica salva permanentemente

### Modo Automático (Recomendado)
1. Vá para a aba "🤖 MODO AUTOMÁTICO"
2. Digite o **Número de Prenotação** (ex: `229885`)
3. Clique em "🚀 INICIAR BUSCA AUTOMÁTICA"
4. Aguarde a busca e extração automática
5. Verifique os **previews** dos documentos
6. Clique em "✅ CONTINUAR" ou "✋ FAZER MANUAL"
7. O relatório será gerado e aberto automaticamente

### Modo Manual
1. Vá para a aba "📝 MODO MANUAL"
2. Selecione o PDF do **Memorial INCRA**
3. Selecione o PDF da **Planta/Projeto**
4. Digite o **Número de Prenotação**
5. Clique em "🔍 COMPARAR DOCUMENTOS"
6. O relatório será gerado e aberto automaticamente

---

## 📁 Estrutura de Arquivos Criada

```
C:\Users\[Usuario]\
├── Documentos\
│   └── Relatórios INCRA\
│       ├── Relatório_INCRA_229885.html
│       ├── Relatório_INCRA_229886.html
│       ├── PDF_INCRAS\
│       │   ├── INCRA_229885_20240115_143022.pdf
│       │   └── INCRA_229886_20240115_150533.pdf
│       └── PDF_PLANTAS\
│           ├── PROJETO_229885_20240115_143022.pdf
│           └── PROJETO_229886_20240115_150533.pdf
└── Downloads\
    └── conferencia_geo_temp\
        ├── 00229885.tif
        ├── 00229885.pdf
        ├── memorial_incra_extraido.pdf
        └── projeto_extraido.pdf
```

---

## 🎨 Comparação de Versões

| Recurso | v3.0 | v4.0 |
|---------|------|------|
| Interface | Básica | ✨ Moderna e Profissional |
| API Key | Campo temporário | 🔑 Salva permanentemente |
| Número Prenotação | - | 📋 Campo obrigatório |
| Salvamento | Botão manual | 💾 Automático |
| Busca TIFF | - | 🔍 Automática (rede) |
| Extração IA | - | 🤖 Totalmente automatizada |
| Preview | - | 👁️ Thumbnails dos PDFs |
| Backup PDFs | - | 💾 Automático |
| Modos | 1 | 2️⃣ Manual + Automático |

---

## 🐛 Solução de Problemas

### "API Key não configurada"
- Clique em "⚙️ Configurar API Key"
- Insira uma chave válida do Google Gemini
- Obtenha em: https://makersuite.google.com/app/apikey

### "Arquivo TIFF não encontrado"
- Verifique se o número de prenotação está correto
- Confirme acesso à rede: `\\192.168.20.100\trabalho\...`
- Use o **Modo Manual** como alternativa

### "Erro ao extrair documentos"
- Verifique se o PDF contém os textos esperados
- Tente usar o **Modo Manual** e selecione os arquivos manualmente

### "Relatório não abre automaticamente"
- Verifique o caminho: `Documentos\Relatórios INCRA\`
- Abra manualmente o arquivo `.html` no navegador

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique este README completo
2. Consulte os logs de erro na interface
3. Teste primeiro com o **Modo Manual** para isolar problemas

---

## 🎉 Conclusão

A **versão 4.0** representa uma evolução completa do sistema, trazendo:
- ✅ **Automação total** do fluxo de trabalho
- ✅ **Interface profissional** e moderna
- ✅ **Inteligência artificial** para extração de documentos
- ✅ **Experiência simplificada** para o usuário
- ✅ **Backup automático** de todos os documentos
- ✅ **Relatórios padronizados** e salvos automaticamente

**Aproveite todas as novas funcionalidades!** 🚀
