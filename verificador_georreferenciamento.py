#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificador de Consistência de Documentos de Georreferenciamento
Aplicação GUI para cartórios - Análise multimodal com Gemini AI
Autor: Sistema Automatizado
Versão: 1.0
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
from pathlib import Path
import threading
from typing import List, Optional

try:
    from pdf2image import convert_from_path
    from PIL import Image, ImageTk
    import google.generativeai as genai
except ImportError as e:
    print(f"❌ Erro: Biblioteca necessária não encontrada: {e}")
    print("\nInstale as dependências com:")
    print("pip install pdf2image Pillow google-generativeai --break-system-packages")
    print("\nNota: Também é necessário ter o 'poppler-utils' instalado no sistema.")
    sys.exit(1)


class VerificadorGeorreferenciamento:
    """Classe principal da aplicação de verificação de documentos."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Verificador de Consistência - Georreferenciamento")
        self.root.geometry("1200x900")
        
        # Configurar fonte padrão maior para melhor legibilidade
        self.root.option_add("*Font", "Arial 12")
        
        # Variáveis para armazenar caminhos dos arquivos
        self.incra_path = tk.StringVar()
        self.projeto_path = tk.StringVar()
        self.api_key = tk.StringVar()

        # Variáveis para armazenar imagens processadas
        self.incra_images: List[Image.Image] = []
        self.projeto_images: List[Image.Image] = []
        
        self._criar_interface()
        
    def _criar_interface(self):
        """Cria todos os elementos da interface gráfica."""
        
        # Frame principal com padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid para expansão
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # ===== SEÇÃO: API KEY =====
        ttk.Label(main_frame, text="🔑 API Key do Gemini:", 
                 font=('Arial', 14, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        api_entry = ttk.Entry(main_frame, textvariable=self.api_key, width=40, show="*", font=('Arial', 12))
        api_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 10), padx=(10, 0))
        
        # ===== SEÇÃO: SELEÇÃO DE ARQUIVOS =====
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(main_frame, text="📄 Documentos:", 
                 font=('Arial', 14, 'bold')).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # INCRA
        self._criar_linha_arquivo(main_frame, 3, "INCRA:", self.incra_path)

        # Projeto/Planta
        self._criar_linha_arquivo(main_frame, 4, "Projeto/Planta:", self.projeto_path)
        
        # ===== SEÇÃO: BOTÕES DE AÇÃO =====
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=15)
        
        # Estilo para botões maiores
        style = ttk.Style()
        style.configure('Large.TButton', font=('Arial', 12, 'bold'), padding=10)
        
        # Botão de Comparação com IA
        botoes_ia_frame = ttk.Frame(button_frame)
        botoes_ia_frame.pack(pady=5)

        self.btn_comparar = ttk.Button(
            botoes_ia_frame,
            text="🔍  Comparar INCRA vs. Projeto",
            command=self._comparar_documentos,
            style='Large.TButton',
            width=35
        )
        self.btn_comparar.pack(pady=5)

        # Botão de Comparação Manual
        botoes_manual_frame = ttk.Frame(button_frame)
        botoes_manual_frame.pack(pady=5)
        
        self.btn_comparacao_manual = ttk.Button(
            botoes_manual_frame,
            text="👁️  Comparação Visual Manual",
            command=self._abrir_comparacao_manual,
            style='Large.TButton',
            width=40
        )
        self.btn_comparacao_manual.pack()
        
        # ===== SEÇÃO: ÁREA DE RESULTADOS =====
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(main_frame, text="📋 Relatório de Comparação:", 
                 font=('Arial', 14, 'bold')).grid(row=9, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Frame para área de texto com barra de rolagem
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        # Área de texto com scroll e fonte maior
        self.resultado_text = scrolledtext.ScrolledText(
            text_frame, 
            width=85, 
            height=22,
            wrap=tk.WORD,
            font=('Consolas', 11),
            bg='#ffffff',
            fg='#000000'
        )
        self.resultado_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Botão para salvar HTML
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=11, column=0, columnspan=2, pady=(5, 0))
        
        self.btn_salvar_html = ttk.Button(
            btn_frame,
            text="💾 Salvar Relatório em HTML",
            command=self._salvar_relatorio_html,
            state='disabled'
        )
        self.btn_salvar_html.pack(side=tk.LEFT, padx=5)
        
        # Configurar expansão da área de texto
        main_frame.rowconfigure(10, weight=1)
        
        # Barra de status com fonte maior
        self.status_label = ttk.Label(main_frame, text="✅ Sistema Pronto para Uso", 
                                      relief=tk.SUNKEN, anchor=tk.W, font=('Arial', 11))
        self.status_label.grid(row=12, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Variável para armazenar o HTML do último relatório
        self.ultimo_relatorio_html = ""
        
    def _criar_linha_arquivo(self, parent, row, label_text, text_var):
        """Cria uma linha com label, entry e botão para seleção de arquivo."""
        ttk.Label(parent, text=label_text, font=('Arial', 13)).grid(row=row, column=0, sticky=tk.W, pady=8)
        
        entry_frame = ttk.Frame(parent)
        entry_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))
        entry_frame.columnconfigure(0, weight=1)
        
        entry = ttk.Entry(entry_frame, textvariable=text_var, font=('Arial', 11))
        entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        btn = ttk.Button(entry_frame, text="📁 Selecionar", 
                        command=lambda: self._selecionar_arquivo(text_var))
        btn.configure(width=15)
        btn.grid(row=0, column=1)
        
    def _selecionar_arquivo(self, text_var):
        """Abre diálogo para seleção de arquivo PDF."""
        filename = filedialog.askopenfilename(
            title="Selecione o arquivo PDF",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if filename:
            text_var.set(filename)
            
    def _salvar_relatorio_html(self):
        """Salva o relatório atual em arquivo HTML."""
        if not self.ultimo_relatorio_html:
            messagebox.showwarning("Aviso", "Nenhum relatório para salvar. Execute uma análise primeiro.")
            return
            
        # Abrir diálogo para salvar arquivo
        filename = filedialog.asksaveasfilename(
            title="Salvar Relatório",
            defaultextension=".html",
            filetypes=[("HTML Files", "*.html"), ("All Files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.ultimo_relatorio_html)
                messagebox.showinfo("Sucesso", f"Relatório salvo em:\n{filename}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar arquivo:\n{str(e)}")
    
    def _abrir_comparacao_manual(self):
        """Abre janela de comparação visual manual dos documentos."""
        # Verificar se há documentos carregados
        if not self.incra_path.get():
            messagebox.showwarning(
                "Aviso",
                "Por favor, selecione o arquivo INCRA."
            )
            return

        if not self.projeto_path.get():
            messagebox.showwarning(
                "Aviso",
                "Por favor, selecione o arquivo do Projeto."
            )
            return

        # Criar e abrir janela de comparação
        try:
            janela_comparacao = JanelaComparacaoManual(
                self.root,
                self.incra_path.get(),
                self.projeto_path.get()
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir comparação manual:\n{str(e)}")
    
    def _validar_entrada(self) -> bool:
        """Valida se todos os campos necessários foram preenchidos."""
        if not self.api_key.get().strip():
            messagebox.showerror("Erro", "Por favor, insira a API Key do Gemini.")
            return False

        if not self.incra_path.get():
            messagebox.showerror("Erro", "Por favor, selecione o arquivo INCRA.")
            return False

        if not self.projeto_path.get():
            messagebox.showerror("Erro", "Por favor, selecione o arquivo Projeto/Planta.")
            return False

        return True
        
    def _atualizar_status(self, mensagem: str):
        """Atualiza a barra de status."""
        self.status_label.config(text=mensagem)
        self.root.update_idletasks()
        
    def _desabilitar_botoes(self):
        """Desabilita os botões durante o processamento."""
        self.btn_comparar.config(state='disabled')
        self.btn_comparacao_manual.config(state='disabled')

    def _habilitar_botoes(self):
        """Reabilita os botões após o processamento."""
        self.btn_comparar.config(state='normal')
        self.btn_comparacao_manual.config(state='normal')
        
    def _carregar_pdf_como_imagens(self, pdf_path: str, rotacionar_90: bool = False) -> List[Image.Image]:
        """
        Converte um PDF em lista de imagens PIL.
        
        Args:
            pdf_path: Caminho do arquivo PDF
            rotacionar_90: Se True, rotaciona as imagens 90 graus (para INCRA)
            
        Returns:
            Lista de objetos PIL.Image
        """
        try:
            self._atualizar_status(f"Convertendo PDF: {Path(pdf_path).name}...")
            
            # Converter PDF para imagens
            images = convert_from_path(pdf_path, dpi=200)
            
            # Rotacionar se necessário (INCRA em paisagem)
            if rotacionar_90:
                self._atualizar_status(f"Rotacionando imagens do INCRA...")
                images = [img.rotate(-90, expand=True) for img in images]
                
            return images
            
        except Exception as e:
            raise Exception(f"Erro ao processar PDF {Path(pdf_path).name}: {str(e)}")
            
    def _construir_prompt_gemini(self) -> List:
        """
        Constrói o prompt multimodal para a API do Gemini.

        Returns:
            Lista contendo strings de texto e objetos PIL.Image para comparação INCRA vs Projeto
        """
        prompt = [
            "Você é um assistente ESPECIALISTA em análise de documentos de georreferenciamento de imóveis rurais para cartórios no Brasil.",
            "\n═══════════════════════════════════════════════════════════",
            "\n=== INSTRUÇÕES CRÍTICAS DE EXTRAÇÃO ===",
            "\n═══════════════════════════════════════════════════════════",
            "\n",
            "\n⚠️⚠️⚠️ ATENÇÃO MÁXIMA - ERROS COMUNS A EVITAR ⚠️⚠️⚠️",
            "\n",
            "\n❌ NÃO CONFUNDA:",
            "\n1. CPF (formato XXX.XXX.XXX-XX) ≠ Código INCRA (formato XXX.XXX.XXX.XXX-X)",
            "\n   • CPF: 765.656.618-04 (pessoa física)",
            "\n   • Código INCRA: 951.742.953-1 (imóvel rural)",
            "\n   • São COMPLETAMENTE diferentes!",
            "\n",
            "\n2. Nomes de proprietários DIFERENTES = STATUS ❌ (não ⚠️!)",
            "\n   • 'PAULO EDUARDO HOTZ' ≠ 'Paulo Gemma Henge'",
            "\n   • São PESSOAS DIFERENTES! Marque como ❌ ERRO GRAVE!",
            "\n   • Não diga 'pequena divergência' - é ERRO TOTAL!",
            "\n",
            "\n3. Memorial em texto corrido TEM perímetro - PROCURE NO TEXTO!",
            "\n   • Busque por: 'perímetro de X metros' ou 'perímetro de X m'",
            "\n   • Exemplo: 'Perímetro (m): 3.873,67 m' ou 'perímetro de 3.873,67 metros'",
            "\n   • Se encontrar, extraia! Não diga 'Não encontrado'!",
            "\n",
            "\n4. Projeto/Planta tem TABELAS - LEIA A TABELA COMPLETA!",
            "\n   • Projetos em PDF digital têm tabelas de coordenadas",
            "\n   • Procure por colunas: Código, Longitude, Latitude, Altitude",
            "\n   • Ou: Código, E (Este), N (Norte)",
            "\n   • EXTRAIA TODOS OS VÉRTICES DA TABELA!",
            "\n   • Não invente coordenadas - copie da tabela!",
            "\n",
            "\n**FORMATO DOS DOCUMENTOS:**",
            "\n1. 📋 INCRA: Dados em TABELAS - extraia TODAS as células com precisão",
            "\n2. 🗺️ PROJETO/PLANTA: ",
            "\n   • Se for PDF DIGITAL (texto selecionável): TEM TABELAS! Leia-as!",
            "\n   • Se for ESCANEADO (imagem): Extraia visualmente",
            "\n   • Procure por 'Tabela de Coordenadas' ou grade com vértices",
            "\n   • NO PROJETO que você está analisando agora: HÁ UMA TABELA NO CANTO!",
            "\n",
            "\n**⚠️ ATENÇÃO MÁXIMA AO LER PROJETO/PLANTA:**",
            "\n",
            "\n🎯 O PROJETO TEM UMA TABELA! Exemplo:",
            "\n```",
            "\nCódigo      | Longitude        | Latitude         | Altitude",
            "\nAKE-V-0166  | 48°34'14,782\" W | 20°50'45,291\" S | 532,78",
            "\nAKE-M-1028  | 48°34'13,821\" W | 20°50'46,394\" S | 533,92",
            "\n```",
            "\n",
            "\nOU formato UTM:",
            "\n```",
            "\nCódigo      | E (Este)  | N (Norte)",
            "\nAKE-V-0166  | 741319    | 7696237",
            "\n```",
            "\n",
            "\nVocê DEVE:",
            "\n✅ Procurar pela tabela (geralmente no canto ou no topo)",
            "\n✅ Ler TODAS as linhas da tabela",
            "\n✅ Extrair TODOS os vértices listados",
            "\n✅ Copiar coordenadas EXATAMENTE como na tabela",
            "\n✅ Se houver 26 vértices na tabela, liste os 26!",
            "\n✅ NÃO invente coordenadas - só o que está na tabela",
            "\n",
            "\n**EQUIVALÊNCIAS SEMÂNTICAS (MUITO IMPORTANTE!):**",
            "\n- '19,0211 ha' = 'Área: 19.0211 hectares' = 'ÁREA TOTAL (ha): 19,0211'",
            "\n- 'José da Silva' = 'Sr. José da Silva' = 'JOSÉ DA SILVA' = 'Jose da Silva'",
            "\n- Vírgula e ponto decimal são equivalentes: 19,02 = 19.02",
            "\n- Espaços e formatação diferentes não importam",
            "\n",
            "\n**⚠️ MAS ATENÇÃO - QUANDO NÃO É EQUIVALENTE:**",
            "\n- 'PAULO EDUARDO HOTZ' ≠ 'Paulo Gemma Henge' → São PESSOAS DIFERENTES! Status = ❌",
            "\n- '951.742.953-1' ≠ '765.656.618-04' → Um é Código INCRA, outro é CPF! Status = ❌",
            "\n- '3.873,67 m' ≠ 'Não encontrado' → Um tem valor, outro não! Status = ❌",
            "\n- 'Latitude/Longitude' ≠ 'UTM' → Sistemas DIFERENTES! Status = ⚠️",
            "\n",
            "\n**⚠️ ATENÇÃO ESPECIAL - INFORMAÇÕES PARCIAIS:**",
            "\n- Se um documento tem TEXTO PARCIAL de outro, isso NÃO é igual!",
            "\n- Quando encontrar casos assim, marque como <span class='status-alerta'>⚠️</span>",
            "\n- E adicione observação: 'VERIFICAR: Um documento tem informação mais completa'",
            "\n- O usuário DEVE verificar manualmente se a informação adicional é relevante",
            "\n",
            "\n**DADOS QUE VOCÊ DEVE EXTRAIR DE CADA DOCUMENTO:**",
            "\n",
            "\n✅ **DADOS BÁSICOS:**",
            "\n   • Proprietário(s) - nome completo EXATO",
            "\n   • Nome do Imóvel/Propriedade",
            "\n   • Matrícula(s) do cartório",
            "\n   • Município e Estado (UF)",
            "\n   • Código INCRA (código de certificação) - NÃO CONFUNDA COM CPF!",
            "\n   • CCIR (se houver)",
            "\n   • Cartório/CNS",
            "\n",
            "\n✅ **DADOS TÉCNICOS:**",
            "\n   • Área Total em hectares (todas as casas decimais)",
            "\n   • Perímetro em metros",
            "\n   • Sistema de coordenadas (UTM/Geográfico/SIRGAS)",
            "\n   • Datum (SIRGAS2000, SAD69, etc)",
            "\n",
            "\n✅ **VÉRTICES E COORDENADAS - ⚠️ MÁXIMA ATENÇÃO:**",
            "\n   • TODOS os vértices (V1, V2, V3, V4, V5, V6...)",
            "\n   • Códigos COMPLETOS dos vértices (ex: NCXC-P-1032, YGGA-M-0046, AKE-V-0166)",
            "\n   • ⚠️ COPIE O CÓDIGO EXATAMENTE LETRA POR LETRA!",
            "\n   • Coordenadas COMPLETAS de cada vértice:",
            "\n     - Longitude (ex: -48°40'19,003\") OU E=741319 (UTM)",
            "\n     - Latitude (ex: -21°00'03,754\") OU N=7696237 (UTM)",
            "\n     - Altitude se houver (ex: 509,05 m)",
            "\n   • CRÍTICO: Não omita vértices! Liste TODOS que encontrar!",
            "\n   • No Projeto, os vértices estão em TABELAS:",
            "\n     Procure por tabela com colunas: Código | Longitude | Latitude | Altitude",
            "\n     Ou: Código | E | N",
            "\n",
            "\n✅ **CONFRONTANTES/LIMITES:**",
            "\n   • Norte: [quem/o quê]",
            "\n   • Sul: [quem/o quê]",
            "\n   • Leste: [quem/o quê]",
            "\n   • Oeste: [quem/o quê]",
            "\n",
            "\n--- INÍCIO DOCUMENTO INCRA ---",
            "\n",
            "\n🚨🚨🚨 ALERTA CRÍTICO - CÓDIGOS DOS VÉRTICES 🚨🚨🚨",
            "\n",
            "\n⚠️⚠️⚠️ PROBLEMA COMUM DE OCR:",
            "\nO OCR frequentemente CONFUNDE a letra 'K' com 'M'!",
            "\n",
            "\n❌ ERRO GRAVÍSSIMO:",
            "\n   AME-V-0166  ← ERRADO! (K virou M)",
            "\n   AME-M-1028  ← ERRADO! (K virou M)",
            "\n   AME-P-3567  ← ERRADO! (K virou M)",
            "\n",
            "\n✅ CÓDIGOS CORRETOS:",
            "\n   AKE-V-0166  ← CORRETO! (com K)",
            "\n   AKE-M-1028  ← CORRETO! (com K)",
            "\n   AKE-P-3567  ← CORRETO! (com K)",
            "\n",
            "\n🔍 COMO IDENTIFICAR:",
            "\nOlhe com ATENÇÃO EXTREMA para as primeiras 3 letras do código:",
            "\n• Se parece 'AME' → É ERRO! Deve ser 'AKE'",
            "\n• Se parece 'AXE' → É ERRO! Deve ser 'AKE'",
            "\n• Se parece 'AKF' → É ERRO! Deve ser 'AKE'",
            "\n",
            "\n💡 DICA:",
            "\nNeste documento, o código de credenciamento é 'AKE'.",
            "\nPORTANTO, TODOS os vértices começam com 'AKE-'!",
            "\n",
            "\n⚠️ NUNCA NUNCA NUNCA escreva 'AME'!",
            "\n⚠️ SEMPRE escreva 'AKE' com a letra K!",
            "\n",
            "\n🎯 EXTRAÇÃO ESPECÍFICA DO INCRA - INSTRUÇÕES CIRÚRGICAS",
            "\n",
            "\n════════════════════════════════════════════════════════════",
            "\n                PARTE 1: DADOS CADASTRAIS                   ",
            "\n════════════════════════════════════════════════════════════",
            "\n",
            "\nExtraia APENAS as seguintes informações, NESTA ORDEM:",
            "\n",
            "\n1️⃣ **Denominação:**",
            "\n   • PROCURE: Linha que começa com 'Denominação:'",
            "\n   • EXTRAIA: SOMENTE o nome do imóvel",
            "\n   • REMOVA: Qualquer menção a 'Área X', 'Matrícula', números",
            "\n   • EXEMPLO:",
            "\n     ❌ Errado: 'Fazenda Monte Rosa - Área 2 – Matrícula n° 27.935'",
            "\n     ✅ Correto: 'Fazenda Monte Rosa'",
            "\n",
            "\n2️⃣ **Proprietário(a):**",
            "\n   • PROCURE: Linha que começa com 'Proprietário(a):'",
            "\n   • EXTRAIA: Nome completo do proprietário",
            "\n   • EXEMPLO: 'RENÊ EDUARDO HOTZ'",
            "\n",
            "\n3️⃣ **Matrícula do imóvel:**",
            "\n   • PROCURE: Linha 'Matrícula do imóvel:'",
            "\n   • ATENÇÃO: Pode ter continuação na página 3!",
            "\n   • EXTRAIA: TODOS os números de matrícula",
            "\n   • EXEMPLO: '28625, 28626, 27935, 27936, 11798'",
            "\n   • LEMBRE: Procurar também: 'continuação da página 1: ...'",
            "\n",
            "\n4️⃣ **Município/UF:**",
            "\n   • PROCURE: 'Município/UF:'",
            "\n   • EXTRAIA: Nome do município e UF",
            "\n   • EXEMPLO: 'Bebedouro-SP'",
            "\n",
            "\n5️⃣ **Código de credenciamento:**",
            "\n   • PROCURE: 'Código de credenciamento:'",
            "\n   • EXTRAIA: O código (geralmente 3 letras)",
            "\n   • EXEMPLO: 'AKE'",
            "\n",
            "\n6️⃣ **Código INCRA/SNCR:**",
            "\n   • PROCURE: 'Código INCRA/SNCR:'",
            "\n   • EXTRAIA: Código completo",
            "\n   • EXEMPLO: '6120730013504'",
            "\n   • ⚠️ NÃO confunda com CPF!",
            "\n",
            "\n7️⃣ **Área (Sistema Geodésico Local):**",
            "\n   • PROCURE: 'Área (Sistema Geodésico Local):'",
            "\n   • EXTRAIA: Valor e unidade",
            "\n   • EXEMPLO: '68,7187 ha'",
            "\n",
            "\n8️⃣ **Perímetro (m):**",
            "\n   • PROCURE: 'Perímetro (m):'",
            "\n   • EXTRAIA: Valor em metros",
            "\n   • EXEMPLO: '3.873,67 m'",
            "\n",
            "\n════════════════════════════════════════════════════════════",
            "\n              PARTE 2: TABELA DE COORDENADAS                ",
            "\n════════════════════════════════════════════════════════════",
            "\n",
            "\n📊 LOCALIZAÇÃO DA TABELA:",
            "\n   • Título: 'DESCRIÇÃO DA PARCELA'",
            "\n   • Tem 2 seções lado a lado:",
            "\n     - VÉRTICE (esquerda): Código, Longitude, Latitude, Altitude",
            "\n     - SEGMENTO VANTE (direita): Código, Azimute, Dist.(m), Confrontações",
            "\n",
            "\n⚠️ INSTRUÇÕES CRÍTICAS PARA LER A TABELA:",
            "\n",
            "\n🚨🚨🚨 REGRA ABSOLUTA - EXTRAÇÃO COMPLETA 🚨🚨🚨",
            "\n",
            "\n⛔ ZERO TOLERÂNCIA PARA LINHAS FALTANDO:",
            "\n• Você DEVE extrair 100% das linhas da tabela",
            "\n• NÃO pule NENHUMA linha",
            "\n• NÃO omita NENHUM vértice ou segmento",
            "\n• MANTENHA a ordem EXATA do documento original",
            "\n• LEIA linha por linha, da primeira até a ÚLTIMA",
            "\n• Se a tabela tem 26 linhas, seu relatório DEVE ter 26 linhas",
            "\n• Se a tabela tem 30 linhas, seu relatório DEVE ter 30 linhas",
            "\n",
            "\n📊 MÉTODO DE EXTRAÇÃO LINHA POR LINHA:",
            "\n1. Comece na primeira linha de dados (após o cabeçalho)",
            "\n2. Leia e extraia: linha 1, linha 2, linha 3, linha 4...",
            "\n3. Continue SEM PULAR até a última linha",
            "\n4. CONTE quantas linhas você extraiu",
            "\n5. VERIFIQUE: O número de linhas extraídas = número de linhas na tabela?",
            "\n6. Se NÃO, VOLTE e extraia as linhas que faltam!",
            "\n",
            "\n✅ VERIFICAÇÃO OBRIGATÓRIA:",
            "\nApós a extração, PERGUNTE A SI MESMO:",
            "\n• Quantas linhas de vértices tem na tabela? _____",
            "\n• Quantas linhas de vértices eu extraí? _____",
            "\n• Os números são IGUAIS? Se NÃO, falta algo!",
            "\n",
            "\n════════════════════════════════════════════════════════════",
            "\n      🎯 ESTRATÉGIA DE EXTRAÇÃO EM DUAS ETAPAS 🎯",
            "\n════════════════════════════════════════════════════════════",
            "\n",
            "\n🚨🚨🚨 IMPORTANTE: O INCRA É A FONTE DE VERDADE! 🚨🚨🚨",
            "\n",
            "\n📋 ETAPA 1 - EXTRAIR CÓDIGOS DO INCRA PRIMEIRO:",
            "\n",
            "\n1️⃣ ANTES de fazer qualquer comparação, LEIA APENAS a coluna 'Código' do INCRA",
            "\n2️⃣ Extraia TODOS os códigos da tabela do INCRA em uma lista",
            "\n3️⃣ Esta lista será sua FONTE DE VERDADE",
            "\n",
            "\n💡 POR QUÊ?",
            "\n• O documento INCRA tem os códigos mais legíveis",
            "\n• Os códigos do PROJETO são os MESMOS do INCRA",
            "\n• Os códigos do SEGMENTO VANTE também são os MESMOS",
            "\n",
            "\n✅ EXEMPLO DE LISTA DE CÓDIGOS:",
            "\nVÉRTICES:",
            "\n  AKE-V-0166  ← Primeiro vértice",
            "\n  AKE-M-1028",
            "\n  AKE-M-1029",
            "\n  AKE-M-1087  ← ⚠️ É 1087, NÃO 1098 ou 1069!",
            "\n  AKE-M-1088  ← ⚠️ É 1088, NÃO 1099 ou 1089!",
            "\n  AKE-P-3567",
            "\n  AKE-P-3568",
            "\n  AKE-P-3569",
            "\n  ...",
            "\n  AKE-P-3584",
            "\n  AKE-P-3585",
            "\n  AKE-P-3586  ← Último vértice (número mais alto)",
            "\n",
            "\n🚨🚨🚨 REGRA IMPORTANTE - SEQUÊNCIA DE CÓDIGOS 🚨🚨🚨",
            "\n",
            "\n⚠️ CÓDIGOS SEGUEM ORDEM CRESCENTE:",
            "\n• Se começa com 1028, continua: 1029, 1030, 1087, 1088...",
            "\n• Se está em 3567, continua: 3568, 3569, 3570... 3584, 3585, 3586",
            "\n• Números SEMPRE CRESCEM, NUNCA VOLTAM!",
            "\n• Se chegou em AKE-P-3586, o próximo NÃO pode ser AKE-V-0166",
            "\n",
            "\n⚠️ O PRIMEIRO VÉRTICE NÃO É O ÚLTIMO:",
            "\n• Primeiro vértice: AKE-V-0166 (número baixo: 0166)",
            "\n• Último vértice: AKE-P-3586 (número alto: 3586)",
            "\n• ❌ ERRADO: ...AKE-P-3585, AKE-P-3586, AKE-V-0166 (0166 < 3586!)",
            "\n• ✅ CORRETO: ...AKE-P-3585, AKE-P-3586 (para aqui!)",
            "\n",
            "\n💡 NOTA SOBRE FECHAMENTO DE POLÍGONO:",
            "\n• Algumas tabelas mostram o primeiro vértice novamente no FINAL",
            "\n• Isso é apenas para indicar que o polígono fecha",
            "\n• Mas na LISTA DE CÓDIGOS, NÃO repita o primeiro!",
            "\n• Exemplo: Se tem 26 vértices, liste 26 códigos únicos",
            "\n",
            "\nSEGMENTO VANTE:",
            "\n  (mesmos códigos, na segunda parte da tabela INCRA)",
            "\n",
            "\n📋 ETAPA 2 - USAR CÓDIGOS DE REFERÊNCIA NO PROJETO:",
            "\n",
            "\n1️⃣ Quando for ler a tabela do PROJETO",
            "\n2️⃣ Use a LISTA DE CÓDIGOS do INCRA como referência",
            "\n3️⃣ Procure no PROJETO as coordenadas correspondentes a cada código",
            "\n4️⃣ Os códigos são IDÊNTICOS nos dois documentos",
            "\n",
            "\n🔴 NÃO FAÇA OCR dos códigos do Projeto se não tiver certeza!",
            "\n🟢 USE os códigos do INCRA como referência!",
            "\n",
            "\n════════════════════════════════════════════════════════════",
            "\n",
            "\n1. LOCALIZE a tabela 'DESCRIÇÃO DA PARCELA'",
            "\n",
            "\n2. A tabela tem este formato:",
            "\n┌─────────────┬────────────────┬────────────────┬─────────────┐",
            "\n│ VÉRTICE                                                      │",
            "\n├─────────────┼────────────────┼────────────────┼─────────────┤",
            "\n│ Código      │ Longitude      │ Latitude       │ Altitude(m) │",
            "\n├─────────────┼────────────────┼────────────────┼─────────────┤",
            "\n│ AKE-V-0166  │ -48°34'14,782\" │ -20°50'45,291\" │ 532,78      │",
            "\n└─────────────┴────────────────┴────────────────┴─────────────┘",
            "\n",
            "\n┌─────────────┬─────────┬──────────┬─────────────────────────┐",
            "\n│ SEGMENTO VANTE                                              │",
            "\n├─────────────┼─────────┼──────────┼─────────────────────────┤",
            "\n│ Código      │ Azimute │ Dist.(m) │ Confrontações           │",
            "\n├─────────────┼─────────┼──────────┼─────────────────────────┤",
            "\n│ AKE-M-1028  │ 140°40' │ 43,85    │ CNS: 12.102-0 | Mat...  │",
            "\n└─────────────┴─────────┴──────────┴─────────────────────────┘",
            "\n",
            "\n3. COPIE os códigos dos vértices EXATAMENTE - CARACTERE POR CARACTERE:",
            "\n   🚨🚨🚨 EXTREMAMENTE IMPORTANTE: NÃO INVENTE CÓDIGOS! 🚨🚨🚨",
            "\n   • Copie o que ESTÁ ESCRITO, não o que você ACHA que deveria estar!",
            "\n   • Exemplo: AKE-V-0166, AKE-M-1028, AKE-P-3567",
            "\n   • ⚠️ NÃO troque letras: AKE ≠ AME ≠ AXE ≠ AKF",
            "\n   • ⚠️ NÃO troque números: 1028 ≠ 1008 ≠ 1128 ≠ 1030",
            "\n   • ⚠️ Se está 1087, copie 1087 (NÃO mude para 1030!)",
            "\n   • ⚠️ Se está 1088, copie 1088 (NÃO omita!)",
            "\n   • ⚠️ Mantenha hífens: AKE-P-3567 (não AKE P 3567)",
            "\n   • ⚠️⚠️⚠️ UNDERSCORES são DIFERENTES de HÍFENS:",
            "\n       - Se está AKE_P-3568 (com underscore _), copie AKE_P-3568",
            "\n       - Se está AKE-P-3568 (com hífen -), copie AKE-P-3568",
            "\n       - AKE_P ≠ AKE-P (são DIFERENTES!)",
            "\n   • OLHE COM ATENÇÃO: é hífen (-) ou underscore (_)?",
            "\n",
            "\n4. COPIE as coordenadas COM PRECISÃO EXTREMA:",
            "\n   ",
            "\n   🎯 MÉTODO DE EXTRAÇÃO - LEIA DEVAGAR, CARACTERE POR CARACTERE:",
            "\n   ",
            "\n   📍 LONGITUDE (coluna 2):",
            "\n   • Formato: -48°34'14,782\"",
            "\n   • Leia: sinal (-), graus (48), símbolo (°), minutos (34), apóstrofo ('), segundos (14,782), aspas (\")",
            "\n   • ⚠️ CUIDADO: Os segundos têm VÍRGULA e 3 casas decimais: 14,782",
            "\n   • ⚠️ NÃO confunda: 14,782 ≠ 14,78 ≠ 14,7",
            "\n   • ⚠️ NÃO confunda: 34 ≠ 35 ≠ 33",
            "\n   ",
            "\n   📍 LATITUDE (coluna 3):",
            "\n   • Formato: -20°50'45,291\"",
            "\n   • Leia: sinal (-), graus (20), símbolo (°), minutos (50), apóstrofo ('), segundos (45,291), aspas (\")",
            "\n   • ⚠️ CUIDADO: Os segundos têm VÍRGULA e 3 casas decimais: 45,291",
            "\n   • ⚠️ NÃO confunda: 45,291 ≠ 45,29 ≠ 45,2",
            "\n   • ⚠️ NÃO confunda: 50 ≠ 51 ≠ 49",
            "\n   ",
            "\n   📍 ALTITUDE (coluna 4):",
            "\n   • Formato: 532,78",
            "\n   • Número com vírgula e 2 casas decimais",
            "\n   • ⚠️ CUIDADO: 532,78 ≠ 532,77 ≠ 533,78",
            "\n   ",
            "\n   🚨🚨🚨 ATENÇÃO MÁXIMA:",
            "\n   • Coordenadas são EXTREMAMENTE PRECISAS",
            "\n   • Um erro de 1 segundo = ~30 metros de diferença no terreno!",
            "\n   • LEIA DEVAGAR, confira DUAS VEZES cada número",
            "\n   • Use ZOOM na imagem se necessário",
            "\n   ",
            "\n   📍 IMPORTANTE PARA COMPARAÇÃO:",
            "\n   🚨 O INCRA tem sinal negativo (-) antes das coordenadas",
            "\n   🚨 O PROJETO NÃO tem sinal negativo, usa W/S no final",
            "\n   🚨 Na comparação, IGNORE o sinal negativo!",
            "\n   ",
            "\n   ✅ EXEMPLOS EQUIVALENTES (são a MESMA coordenada):",
            "\n   • INCRA: -48°34'14,782\"  ≡  PROJETO: 48°34'14,782\" W",
            "\n   • INCRA: -20°50'45,291\"  ≡  PROJETO: 20°50'45,291\" S",
            "\n   ",
            "\n   💡 Ao comparar:",
            "\n   1. Ignore o sinal negativo (-) do INCRA",
            "\n   2. Ignore a letra W/S do PROJETO",
            "\n   3. Compare apenas os números: 48°34'14,782\" = 48°34'14,782\"",
            "\n   4. Verifique TODAS as casas decimais: 14,782 deve ser exatamente 14,782",
            "\n",
            "\n5. REPRODUZA A TABELA COMPLETA - CONTAGEM OBRIGATÓRIA:",
            "\n   ",
            "\n   🚨 CRÍTICO: A tabela continua em MÚLTIPLAS PÁGINAS!",
            "\n   • Página 1 do INCRA: Primeiros ~16-18 vértices",
            "\n   • Página 2 do INCRA: Vértices restantes (~8-10)",
            "\n   • TOTAL: ~26 vértices (ou mais)",
            "\n   ",
            "\n   📊 MÉTODO DE CONTAGEM:",
            "\n   1. Leia a primeira linha após o cabeçalho",
            "\n   2. CONTE: linha 1, linha 2, linha 3, linha 4...",
            "\n   3. Continue até NÃO haver mais linhas",
            "\n   4. Anote o total: \"Encontrei __ linhas\"",
            "\n   5. Verifique: O último código tem número MAIOR que o primeiro?",
            "\n   ",
            "\n   ⚠️⚠️⚠️ ATENÇÃO COM O FECHAMENTO:",
            "\n   • Algumas tabelas repetem o PRIMEIRO vértice no final",
            "\n   • Isso serve para \"fechar o polígono\" visualmente",
            "\n   • MAS você NÃO deve contar essa linha repetida!",
            "\n   ",
            "\n   ✅ EXEMPLO CORRETO:",
            "\n   Linha 1: AKE-V-0166 (primeiro - número 0166)",
            "\n   Linha 2: AKE-M-1028",
            "\n   ...",
            "\n   Linha 25: AKE-P-3585",
            "\n   Linha 26: AKE-P-3586 (último - número 3586)",
            "\n   [Linha extra: AKE-V-0166] ← NÃO CONTE ESTA! É repetição!",
            "\n   Total de vértices únicos: 26",
            "\n   ",
            "\n   ❌ EXEMPLO ERRADO:",
            "\n   Linha 25: AKE-P-3585",
            "\n   Linha 26: AKE-P-3586",
            "\n   Linha 27: AKE-V-0166 ← ERRO! 0166 < 3586 (voltou!)",
            "\n   ",
            "\n   💡 REGRA SIMPLES:",
            "\n   • Se o código tem número MENOR que o anterior = É REPETIÇÃO",
            "\n   • Pare de contar quando o número voltar ao início",
            "\n   ",
            "\n   ⚠️ NUNCA pare de ler na página 1!",
            "\n   ⚠️ SEMPRE verifique se há mais páginas!",
            "\n   ⚠️ Se você extraiu 25 vértices, PROCURE O 26º!",
            "\n   ",
            "\n   🚨🚨🚨 ATENÇÃO ESPECIAL - O ÚLTIMO CÓDIGO:",
            "\n   ⚠️⚠️⚠️ O ÚLTIMO CÓDIGO É O MAIS IMPORTANTE! ⚠️⚠️⚠️",
            "\n   ",
            "\n   • Você DEVE encontrar e extrair o ÚLTIMO código da tabela",
            "\n   • Procure na SEGUNDA PÁGINA do INCRA!",
            "\n   • O último código tem o NÚMERO MAIS ALTO",
            "\n   • Exemplo: Se tem AKE-P-3586, esse é o ÚLTIMO (3586 é o maior)",
            "\n   • NÃO PODE FALTAR! Isso é CRÍTICO!",
            "\n   ",
            "\n   ✅ VERIFICAÇÃO DO ÚLTIMO CÓDIGO:",
            "\n   1. Qual é o último código que extraí? _______",
            "\n   2. Esse código tem o número mais alto da tabela? SIM/NÃO",
            "\n   3. Verifiquei a segunda página do INCRA? SIM/NÃO",
            "\n   4. Há alguma linha depois desse código? SIM/NÃO",
            "\n   ",
            "\n   🔴 Se alguma resposta não estiver certa, PROCURE NOVAMENTE!",
            "\n",
            "\n5.5 USE O OCR DO GEMINI PARA NÚMEROS:",
            "\n   ",
            "\n   🎯 INSTRUÇÕES ESPECIAIS PARA RECONHECIMENTO DE NÚMEROS:",
            "\n   ",
            "\n   Você tem capacidade multimodal (visão) do Gemini!",
            "\n   USE essa capacidade para ler números com PRECISÃO MÁXIMA!",
            "\n   ",
            "\n   📍 MÉTODO DE OCR PARA COORDENADAS:",
            "\n   ",
            "\n   1️⃣ LONGITUDE (coluna 2):",
            "\n   • FOQUE na coluna de Longitude",
            "\n   • Faça OCR caractere por caractere",
            "\n   • Formato: -48°34'14,782\"",
            "\n   • CUIDADO com números similares: 3≠8, 1≠7, 4≠9, 5≠6",
            "\n   • Os segundos têm 3 casas decimais: X,XXX",
            "\n   • Exemplos de erros comuns:",
            "\n     - 14,782 lido como 14,78 ← ERRADO! Faltam dígitos!",
            "\n     - 34 lido como 39 ← ERRADO! Confundiu 4 com 9!",
            "\n   ",
            "\n   2️⃣ LATITUDE (coluna 3):",
            "\n   • FOQUE na coluna de Latitude",
            "\n   • Faça OCR caractere por caractere",
            "\n   • Formato: -20°50'45,291\"",
            "\n   • CUIDADO com números similares: 0≠8, 5≠6, 2≠7",
            "\n   • Os segundos têm 3 casas decimais: X,XXX",
            "\n   • Exemplos de erros comuns:",
            "\n     - 45,291 lido como 45,29 ← ERRADO! Faltam dígitos!",
            "\n     - 50 lido como 58 ← ERRADO! Confundiu 0 com 8!",
            "\n   ",
            "\n   3️⃣ ALTITUDE (m) (coluna 4):",
            "\n   🚨🚨🚨 ALTITUDE É A QUE MAIS TEM ERRO! ATENÇÃO MÁXIMA! 🚨🚨🚨",
            "\n   ",
            "\n   • FOQUE EXCLUSIVAMENTE na coluna 'Altitude(m)'",
            "\n   • USE OCR com máxima atenção",
            "\n   • Formato: XXX,XX (3 dígitos, vírgula, 2 decimais)",
            "\n   • Exemplos: 532,78 ou 533,92 ou 534,14",
            "\n   • CUIDADO com números similares:",
            "\n     - 5 vs 6 (muito similares!)",
            "\n     - 3 vs 8 (muito similares!)",
            "\n     - 2 vs 7 (muito similares!)",
            "\n     - 1 vs 7 (muito similares!)",
            "\n   • SEMPRE tem 2 casas decimais após a vírgula",
            "\n   • Exemplos de erros comuns:",
            "\n     - 532,78 lido como 537,78 ← Confundiu 2 com 7!",
            "\n     - 533,92 lido como 538,92 ← Confundiu 3 com 8!",
            "\n     - 534,14 lido como 534,1 ← Falta o último dígito!",
            "\n   ",
            "\n   💡 DICA IMPORTANTE:",
            "\n   • Para cada número, OLHE COM ATENÇÃO",
            "\n   • Compare com números similares na mesma tabela",
            "\n   • Se tiver dúvida entre 532 e 537, veja outros números",
            "\n   • Use contexto: altitudes geralmente variam pouco (530-540)",
            "\n",
            "\n6. MANTENHA A FORMATAÇÃO:",
            "\n   • Use espaços/tabs para alinhar colunas",
            "\n   • Separe seções (VÉRTICE e SEGMENTO VANTE)",
            "\n   • Mantenha símbolos especiais (°, ', \")",
            "\n",
            "\n7. SEGMENTO VANTE - EXTRAÇÃO SEPARADA:",
            "\n   🚨 IMPORTANTE: O SEGMENTO VANTE deve ser comparado SEPARADAMENTE!",
            "\n   • No INCRA: É a segunda parte da tabela",
            "\n   • Colunas: Código, Azimute, Dist.(m), Confrontações",
            "\n   • O Código do Segmento Vante geralmente é diferente do Código do Vértice",
            "\n   • Exemplo de linha do Segmento Vante:",
            "\n     - Código: AKE-M-1028",
            "\n     - Azimute: 140°40'",
            "\n     - Distância: 43,85 m",
            "\n     - Confrontações: CNS: 12.102-0 | Mat. 28309",
            "\n   • EXTRAIA TODOS os segmentos, não apenas alguns!",
            "\n",
            "\n8. CONFRONTANTES DO INCRA:",
            "\n   • Os confrontantes estão na coluna 'Confrontações' da tabela",
            "\n   • Exemplo: 'CNS: 12.102-0 | Mat. 28309'",
            "\n   • Exemplo: 'Estrada Municipal - BBD 315'",
            "\n   • Exemplo: 'CNS: 12.102-0 | Mat. 34685 | Córrego Lambari'",
            "\n   • ⚠️ NÃO extraia nomes de pessoas!",
            "\n   • ✅ Extraia: Matrícula, nome da estrada, córrego, etc.",
            "\n",
            "\n════════════════════════════════════════════════════════════",
            "\n                    FORMATO DE SAÍDA                         ",
            "\n════════════════════════════════════════════════════════════",
            "\n",
            "\nApresente no seguinte formato:",
            "\n",
            "\n**DADOS CADASTRAIS:**",
            "\nDenominação: [valor]",
            "\nProprietário(a): [valor]",
            "\nMatrícula do imóvel: [valor]",
            "\nMunicípio/UF: [valor]",
            "\nCódigo de credenciamento: [valor]",
            "\nCódigo INCRA/SNCR: [valor]",
            "\nÁrea (Sistema Geodésico Local): [valor]",
            "\nPerímetro (m): [valor]",
            "\n",
            "\n**TABELA DE COORDENADAS:**",
            "\n[Reproduza a tabela completa aqui, mantendo formatação]",
            "\n",
            "\nExtraia CADA dado de CADA célula com MÁXIMA PRECISÃO!",
        ]
        
        # Adicionar imagens do INCRA
        prompt.extend(self.incra_images)
        prompt.append("\n--- FIM DOCUMENTO INCRA ---")

        # Adicionar imagens do Projeto
        if self.projeto_images:
            prompt.append("\n--- INÍCIO PROJETO/PLANTA ---")
            prompt.append("\n🎯 ATENÇÃO ESPECIAL PARA ESTE PROJETO:")
            prompt.append("\nEste é um PDF DIGITAL (não escaneado) - ele contém TABELAS DE DADOS!")
            prompt.append("\n")
            prompt.append("\n📊 ONDE ESTÁ A TABELA:")
            prompt.append("\nProcure por uma tabela com o título:")
            prompt.append("\n'Tabela de Coordenadas - Altitudes - Azimutes - Distâncias'")
            prompt.append("\n")
            prompt.append("\nA tabela tem DUAS partes:")
            prompt.append("\n")
            prompt.append("\n📍 PARTE 1 - VÉRTICE:")
            prompt.append("\n┌──────────┬────────────────┬────────────────┬────────────┐")
            prompt.append("\n│ Código   │ Longitude      │ Latitude       │ Altitude   │")
            prompt.append("\n├──────────┼────────────────┼────────────────┼────────────┤")
            prompt.append("\n│ AKE-V... │ 48°34'14,782\" W│ 20°50'45,291\" S│ 532,78     │")
            prompt.append("\n└──────────┴────────────────┴────────────────┴────────────┘")
            prompt.append("\n")
            prompt.append("\n📐 PARTE 2 - SEGMENTO VANTE (após coluna Altitude):")
            prompt.append("\n┌──────────┬──────────┬────────────┐")
            prompt.append("\n│ Azimute  │ Dist.(m) │ Outros     │")
            prompt.append("\n├──────────┼──────────┼────────────┤")
            prompt.append("\n│ 140°40'  │ 43,85    │ ...        │")
            prompt.append("\n└──────────┴──────────┴────────────┘")
            prompt.append("\n")
            prompt.append("\n🚨 IMPORTANTE: No Projeto, o SEGMENTO VANTE vem LOGO APÓS a coluna Altitude!")
            prompt.append("\n   • Procure por colunas: Azimute, Distância (ou Dist.)")
            prompt.append("\n   • Essas colunas vêm DEPOIS de: Código, Longitude, Latitude, Altitude")
            prompt.append("\n   • EXTRAIA também essas informações para comparação!")
            prompt.append("\n")
            prompt.append("\n🚨🚨🚨 REGRA ABSOLUTA - EXTRAÇÃO COMPLETA (PROJETO) 🚨🚨🚨")
            prompt.append("\n")
            prompt.append("\n⛔ ZERO TOLERÂNCIA PARA LINHAS FALTANDO:")
            prompt.append("\n• Você DEVE extrair 100% das linhas da tabela do PROJETO")
            prompt.append("\n• NÃO pule NENHUMA linha")
            prompt.append("\n• NÃO omita NENHUM vértice")
            prompt.append("\n• MANTENHA a ordem EXATA do documento original")
            prompt.append("\n• LEIA linha por linha sequencialmente")
            prompt.append("\n• Conte: Se tem 26 vértices, extraia os 26!")
            prompt.append("\n")
            prompt.append("\n📊 MÉTODO DE EXTRAÇÃO SEQUENCIAL:")
            prompt.append("\n1. Localize a tabela 'Tabela de Coordenadas...'")
            prompt.append("\n2. Identifique a primeira linha de dados")
            prompt.append("\n3. Extraia: Linha 1 → Linha 2 → Linha 3 → ... → Última linha")
            prompt.append("\n4. NÃO pule linhas intermediárias")
            prompt.append("\n5. CONTE o total de linhas extraídas")
            prompt.append("\n6. COMPARE com o total na tabela original")
            prompt.append("\n")
            prompt.append("\n✅ CHECKLIST DE VERIFICAÇÃO:")
            prompt.append("\n□ Li TODAS as linhas da tabela?")
            prompt.append("\n□ A primeira linha está incluída?")
            prompt.append("\n□ A última linha está incluída?")
            prompt.append("\n□ Não pulei nenhuma linha do meio?")
            prompt.append("\n□ A ordem está correta?")
            prompt.append("\n")
            prompt.append("\n════════════════════════════════════════════════════════════")
            prompt.append("\n")
            prompt.append("\n⚠️ INSTRUÇÕES CRÍTICAS DE EXTRAÇÃO:")
            prompt.append("\n")
            prompt.append("\n1. 🔍 LOCALIZE a tabela completa")
            prompt.append("\n   • Geralmente está no CANTO ESQUERDO da página")
            prompt.append("\n   • Ou na parte SUPERIOR")
            prompt.append("\n   • Título: 'Tabela de Coordenadas...'")
            prompt.append("\n")
            prompt.append("\n2. 📖 LEIA LINHA POR LINHA")
            prompt.append("\n   • Primeira linha: Cabeçalhos (Código, Longitude, Latitude, Altitude)")
            prompt.append("\n   • Depois: TODAS as linhas de dados")
            prompt.append("\n   • Pode ter 20, 26, 30 ou mais vértices!")
            prompt.append("\n")
            prompt.append("\n3. 🎯 USE OS CÓDIGOS DO INCRA COMO REFERÊNCIA!")
            prompt.append("\n   ")
            prompt.append("\n   🚨🚨🚨 ESTRATÉGIA IMPORTANTE 🚨🚨🚨")
            prompt.append("\n   ")
            prompt.append("\n   ✅ Você JÁ extraiu a lista de códigos do INCRA na ETAPA 1")
            prompt.append("\n   ✅ AGORA use essa lista para encontrar as coordenadas no PROJETO")
            prompt.append("\n   ✅ Os códigos são IDÊNTICOS nos dois documentos!")
            prompt.append("\n   ")
            prompt.append("\n   📋 MÉTODO:")
            prompt.append("\n   1. Pegue o primeiro código da sua lista do INCRA (ex: AKE-V-0166)")
            prompt.append("\n   2. PROCURE esse código na tabela do PROJETO")
            prompt.append("\n   3. Extraia as coordenadas (Long, Lat, Alt, Azimute, Dist)")
            prompt.append("\n   4. Repita para o próximo código da lista")
            prompt.append("\n   5. Continue até o último código")
            prompt.append("\n   ")
            prompt.append("\n   🔴 NÃO TENTE ler os códigos do Projeto se não conseguir!")
            prompt.append("\n   🟢 USE a lista de códigos do INCRA que você já tem!")
            prompt.append("\n   ")
            prompt.append("\n   ⚠️ LEMBRE-SE:")
            prompt.append("\n   • Se o INCRA tem AKE-M-1087, o PROJETO também tem AKE-M-1087")
            prompt.append("\n   • Se o INCRA tem AKE-M-1088, o PROJETO também tem AKE-M-1088")
            prompt.append("\n   • Os códigos são EXATAMENTE IGUAIS nos dois documentos!")
            prompt.append("\n   ")
            prompt.append("\n   COORDENADAS NO PROJETO:")
            prompt.append("\n   • Longitude: 48°34'14,782\" W (SEM sinal negativo, COM letra W)")
            prompt.append("\n   • Latitude: 20°50'45,291\" S (SEM sinal negativo, COM letra S)")
            prompt.append("\n   • Altitude: 532,78 (número simples)")
            prompt.append("\n   ")
            prompt.append("\n   🚨 DIFERENÇA INCRA vs PROJETO:")
            prompt.append("\n   • INCRA: -48°34'14,782\" (TEM sinal negativo -)")
            prompt.append("\n   • PROJETO: 48°34'14,782\" W (NÃO tem sinal -, tem letra W)")
            prompt.append("\n   • São EQUIVALENTES! Na comparação, ignore o sinal -")
            prompt.append("\n")
            prompt.append("\n4. ⚠️ NÃO CONFUNDA:")
            prompt.append("\n   • ❌ NÃO pegue números do DESENHO (ex: E=741319 N=7696237)")
            prompt.append("\n   • ❌ NÃO pegue números das LEGENDAS")
            prompt.append("\n   • ❌ NÃO pegue números dos CARIMBOS")
            prompt.append("\n   • ✅ SÓ pegue da TABELA DE COORDENADAS!")
            prompt.append("\n")
            prompt.append("\n5. 📝 LISTE TODOS OS VÉRTICES")
            prompt.append("\n   🚨 CRÍTICO: Extraia TODOS os vértices da tabela!")
            prompt.append("\n   • Se a tabela tem 26 vértices, liste os 26!")
            prompt.append("\n   • Se a tabela tem 30 vértices, liste os 30!")
            prompt.append("\n   • NÃO omita nenhum vértice")
            prompt.append("\n   • NÃO pare em 3-4 vértices")
            prompt.append("\n   • Leia até o FIM da tabela!")
            prompt.append("\n   ")
            prompt.append("\n   🚨🚨🚨 ATENÇÃO ESPECIAL - O ÚLTIMO CÓDIGO DO PROJETO:")
            prompt.append("\n   ⚠️⚠️⚠️ O ÚLTIMO CÓDIGO É O MAIS IMPORTANTE! ⚠️⚠️⚠️")
            prompt.append("\n   ")
            prompt.append("\n   • Você tem a lista de códigos do INCRA")
            prompt.append("\n   • O ÚLTIMO código dessa lista é o que você DEVE encontrar no PROJETO")
            prompt.append("\n   • Exemplo: Se o último do INCRA é AKE-P-3586, PROCURE no PROJETO")
            prompt.append("\n   • NÃO PODE FALTAR! Isso é CRÍTICO!")
            prompt.append("\n   • Se não encontrou, PROCURE NOVAMENTE na tabela do PROJETO")
            prompt.append("\n")
            prompt.append("\n5.5 USE O OCR DO GEMINI PARA NÚMEROS DO PROJETO:")
            prompt.append("\n   ")
            prompt.append("\n   🎯 INSTRUÇÕES ESPECIAIS PARA RECONHECIMENTO DE NÚMEROS:")
            prompt.append("\n   ")
            prompt.append("\n   Você tem capacidade multimodal (visão) do Gemini!")
            prompt.append("\n   USE essa capacidade para ler números com PRECISÃO MÁXIMA!")
            prompt.append("\n   ")
            prompt.append("\n   📍 MÉTODO DE OCR PARA COORDENADAS DO PROJETO:")
            prompt.append("\n   ")
            prompt.append("\n   1️⃣ LONGITUDE:")
            prompt.append("\n   • FOQUE na coluna de Longitude da tabela")
            prompt.append("\n   • Faça OCR caractere por caractere")
            prompt.append("\n   • Formato: 48°34'14,782\" W (SEM sinal -, COM letra W)")
            prompt.append("\n   • CUIDADO com números similares: 3≠8, 1≠7, 4≠9, 5≠6")
            prompt.append("\n   • Os segundos têm 3 casas decimais: X,XXX")
            prompt.append("\n   • NÃO confunda: 14,782 ≠ 14,78")
            prompt.append("\n   ")
            prompt.append("\n   2️⃣ LATITUDE:")
            prompt.append("\n   • FOQUE na coluna de Latitude da tabela")
            prompt.append("\n   • Faça OCR caractere por caractere")
            prompt.append("\n   • Formato: 20°50'45,291\" S (SEM sinal -, COM letra S)")
            prompt.append("\n   • CUIDADO com números similares: 0≠8, 5≠6, 2≠7")
            prompt.append("\n   • Os segundos têm 3 casas decimais: X,XXX")
            prompt.append("\n   • NÃO confunda: 45,291 ≠ 45,29")
            prompt.append("\n   ")
            prompt.append("\n   3️⃣ ALTITUDE (m):")
            prompt.append("\n   🚨🚨🚨 ALTITUDE É A QUE MAIS TEM ERRO! ATENÇÃO MÁXIMA! 🚨🚨🚨")
            prompt.append("\n   ")
            prompt.append("\n   • FOQUE EXCLUSIVAMENTE na coluna Altitude da tabela")
            prompt.append("\n   • USE OCR com máxima atenção")
            prompt.append("\n   • Formato: XXX,XX (3 dígitos, vírgula, 2 decimais)")
            prompt.append("\n   • Exemplos: 532,78 ou 533,92 ou 534,14")
            prompt.append("\n   • CUIDADO com números similares:")
            prompt.append("\n     - 5 vs 6 (confusão comum!)")
            prompt.append("\n     - 3 vs 8 (confusão comum!)")
            prompt.append("\n     - 2 vs 7 (confusão comum!)")
            prompt.append("\n     - 1 vs 7 (confusão comum!)")
            prompt.append("\n   • SEMPRE tem 2 casas decimais após a vírgula")
            prompt.append("\n   • Erros comuns:")
            prompt.append("\n     - 532,78 lido como 537,78 ← Confundiu 2 com 7!")
            prompt.append("\n     - 533,92 lido como 538,92 ← Confundiu 3 com 8!")
            prompt.append("\n     - 534,14 lido como 534,1 ← Falta dígito!")
            prompt.append("\n   ")
            prompt.append("\n   💡 DICA: Compare com os valores do INCRA")
            prompt.append("\n   • Altitude do INCRA e PROJETO devem ser IGUAIS ou muito próximas")
            prompt.append("\n   • Se INCRA tem 532,78 e você leu 537,78 no PROJETO → ERRO!")
            prompt.append("\n   • Use isso para validar sua leitura")
            prompt.append("\n")
            prompt.append("\n💡 EXEMPLO CORRETO DE EXTRAÇÃO:")
            prompt.append("\nVértice AKE-V-0166:")
            prompt.append("\n  • Longitude: 48°34'14,782\" W")
            prompt.append("\n  • Latitude: 20°50'45,291\" S")
            prompt.append("\n  • Altitude: 532,78 m")
            prompt.append("\n")
            prompt.append("\nVértice AKE-M-1028:")
            prompt.append("\n  • Longitude: 48°34'13,821\" W")
            prompt.append("\n  • Latitude: 20°50'46,394\" S")
            prompt.append("\n  • Altitude: 533,92 m")
            prompt.append("\n")
            prompt.append("\n... (continua para TODOS os vértices da tabela)")
            prompt.append("\n")
            prompt.append("\n❌ EXEMPLO ERRADO (NÃO FAÇA ISSO):")
            prompt.append("\n'E=741319 N=7696237' ← Isso é do DESENHO, não da tabela!")
            prompt.append("\n")
            prompt.extend(self.projeto_images)
            prompt.append("\n--- FIM PROJETO/PLANTA ---")

        # INSTRUÇÕES FINAIS CRÍTICAS ANTES DO HTML
        prompt.append("\n")
        prompt.append("\n════════════════════════════════════════════════════════════")
        prompt.append("\n           🚨 LEMBRETE FINAL - ANTES DE GERAR O HTML 🚨")
        prompt.append("\n════════════════════════════════════════════════════════════")
        prompt.append("\n")
        prompt.append("\n⚠️ ANTES de gerar o relatório HTML, VERIFIQUE:")
        prompt.append("\n")
        prompt.append("\n1. ✅ Extraí TODAS as linhas da tabela INCRA?")
        prompt.append("\n   • Contei quantas linhas tem na tabela original?")
        prompt.append("\n   • Contei quantas linhas extraí?")
        prompt.append("\n   • Os números são IGUAIS?")
        prompt.append("\n")
        prompt.append("\n2. ✅ Extraí TODAS as linhas da tabela PROJETO?")
        prompt.append("\n   • Contei quantas linhas tem na tabela original?")
        prompt.append("\n   • Contei quantas linhas extraí?")
        prompt.append("\n   • Os números são IGUAIS?")
        prompt.append("\n")
        prompt.append("\n3. ✅ Mantive a ORDEM EXATA dos documentos originais?")
        prompt.append("\n   • Primeira linha → vem primeiro no relatório")
        prompt.append("\n   • Segunda linha → vem em segundo no relatório")
        prompt.append("\n   • Última linha → vem por último no relatório")
        prompt.append("\n")
        prompt.append("\n4. ✅ NÃO pulei nenhuma linha do meio?")
        prompt.append("\n   • Se tem vértices V-01, V-02, V-03... V-26")
        prompt.append("\n   • Meu relatório tem TODOS eles, em sequência?")
        prompt.append("\n")
        prompt.append("\n4.5 ✅ NÃO repeti o primeiro vértice como último?")
        prompt.append("\n   🚨 VERIFICAÇÃO CRÍTICA DOS CÓDIGOS:")
        prompt.append("\n   • Primeiro código: número baixo (ex: AKE-V-0166 = 0166)")
        prompt.append("\n   • Último código: número alto (ex: AKE-P-3586 = 3586)")
        prompt.append("\n   • ⚠️ Se vejo AKE-V-0166 no final, é REPETIÇÃO (não conte!)")
        prompt.append("\n   • ⚠️ Se o último número é MENOR que o primeiro = ERRO!")
        prompt.append("\n   • ✅ Números devem ser CRESCENTES: 0166 < 1028 < 3586")
        prompt.append("\n   • ❌ ERRADO: ...AKE-P-3586, AKE-V-0166 (voltou para 0166!)")
        prompt.append("\n   • ✅ CORRETO: ...AKE-P-3585, AKE-P-3586 (terminou em 3586)")
        prompt.append("\n")
        prompt.append("\n5. ✅ Extraí TODOS os SEGMENTOS VANTE?")
        prompt.append("\n   🚨🚨🚨 OBRIGATÓRIO: A seção SEGMENTO VANTE deve estar preenchida!")
        prompt.append("\n   • Tanto do INCRA quanto do PROJETO")
        prompt.append("\n   • NO INCRA: Está na segunda parte da tabela (Código, Azimute, Dist., Confrontações)")
        prompt.append("\n   • NO PROJETO: Está após as colunas de coordenadas (colunas Azimute e Distância)")
        prompt.append("\n   • Se não encontrei dados de SEGMENTO VANTE, PROCURE NOVAMENTE!")
        prompt.append("\n   • O relatório HTML DEVE ter a SEÇÃO 4: SEGMENTO VANTE preenchida!")
        prompt.append("\n")
        prompt.append("\n6. ✅ Copiei os CÓDIGOS EXATAMENTE como aparecem?")
        prompt.append("\n   🚨 CRÍTICO: Códigos devem ser copiados CARACTERE POR CARACTERE!")
        prompt.append("\n   • Se está escrito AKE-M-1087, copie AKE-M-1087 (NÃO invente 1030!)")
        prompt.append("\n   • Se está escrito AKE_P-3568 (com underscore), copie AKE_P-3568")
        prompt.append("\n   • Se está escrito AKE-P-3568 (com hífen), copie AKE-P-3568")
        prompt.append("\n   • UNDERSCORES (_) são DIFERENTES de HÍFENS (-)")
        prompt.append("\n   • Números devem ser EXATOS: 1087 ≠ 1030 ≠ 1088")
        prompt.append("\n   • NÃO normalize, NÃO corrija, COPIE EXATAMENTE!")
        prompt.append("\n")
        prompt.append("\n🔴 SE ALGUMA RESPOSTA FOR \"NÃO\": VOLTE E EXTRAIA NOVAMENTE!")
        prompt.append("\n🟢 SE TODAS AS RESPOSTAS FOREM \"SIM\": Prossiga com o HTML!")
        prompt.append("\n")
        prompt.append("\n════════════════════════════════════════════════════════════")
        prompt.append("\n")
        prompt.append("\n🚨🚨🚨 REGRA ABSOLUTA DE RESPOSTA 🚨🚨🚨")
        prompt.append("\n")
        prompt.append("\n⛔ SUA RESPOSTA DEVE COMEÇAR DIRETAMENTE COM: <!DOCTYPE html>")
        prompt.append("\n")
        prompt.append("\n❌ NÃO ESCREVA:")
        prompt.append("\n   • \"OK. Entendido! Vou analisar...\"")
        prompt.append("\n   • \"ANÁLISE DOS DOCUMENTOS:\"")
        prompt.append("\n   • \"DADOS CADASTRAIS:\"")
        prompt.append("\n   • \"TABELA DE COORDENADAS:\"")
        prompt.append("\n   • Qualquer texto explicativo ou rascunho")
        prompt.append("\n")
        prompt.append("\n✅ ESCREVA APENAS:")
        prompt.append("\n   • Primeira linha: <!DOCTYPE html>")
        prompt.append("\n   • Depois: <html>")
        prompt.append("\n   • Depois: todo o HTML do relatório")
        prompt.append("\n   • Última linha: </html>")
        prompt.append("\n")
        prompt.append("\n🔴 NADA ANTES DO <!DOCTYPE html>")
        prompt.append("\n🔴 NADA DEPOIS DO </html>")
        prompt.append("\n🔴 SEM RASCUNHOS, SEM ANÁLISES PRÉVIAS")
        prompt.append("\n🟢 SOMENTE O CÓDIGO HTML PURO!")
        prompt.append("\n")
        prompt.append("\n════════════════════════════════════════════════════════════")
        prompt.append("\n")

        # Instruções de formato de saída - HTML PROFISSIONAL COM CORES

        instrucoes_saida = (
            "\n\n"
            "\n════════════════════════════════════════════════════════════════════"
            "\n                    FORMATO DO RELATÓRIO HTML                       "
            "\n════════════════════════════════════════════════════════════════════"
            "\n"
            "\n🎯 DOCUMENTOS SENDO COMPARADOS: INCRA + PROJETO"
            "\n"
            "\n⚠️⚠️⚠️ REGRA CRÍTICA DE FORMATAÇÃO:"
            "\n"
            "\n1️⃣ Você está comparando: INCRA + PROJETO"
            "\n   • Tabela deve ter 3 colunas: DADO | INCRA | PROJETO | STATUS"
            "\n"
            "\n2️⃣ Estrutura da tabela:"
            "\n   <thead><tr>"
            "\n       <th>DADO</th>"
            "\n       <th>INCRA</th>"
            "\n       <th>PROJETO</th>"
            "\n       <th>STATUS</th>"
            "\n   </tr></thead>"
        )
        
        instrucoes_saida += (
            "\n"
            "\n⚠️ IMPORTANTE: Gere um relatório em HTML completo e profissional."
            "\nUse CSS inline para cores, estilos e organização visual perfeita."
            "\nCada seção deve ter cores diferentes para fácil identificação."
            "\n"
            "\nGere EXATAMENTE este formato HTML (adapte os dados):"
            "\n"
            "\n```html"
            "\n<!DOCTYPE html>"
            "\n<html lang='pt-BR'>"
            "\n<head>"
            "\n    <meta charset='UTF-8'>"
            "\n    <meta name='viewport' content='width=device-width, initial-scale=1.0'>"
            "\n    <title>Relatório de Consistência - Georreferenciamento</title>"
            "\n    <style>"
            "\n        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }"
            "\n        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }"
            "\n        h1 { color: #2c3e50; border-bottom: 4px solid #3498db; padding-bottom: 10px; }"
            "\n        h2 { color: #34495e; margin-top: 30px; padding: 10px; border-left: 5px solid #3498db; background: #ecf0f1; }"
            "\n        .resumo { background: #e8f5e9; padding: 20px; border-left: 5px solid #4caf50; margin: 20px 0; font-size: 16px; }"
            "\n        .resumo.alerta { background: #fff3e0; border-left-color: #ff9800; }"
            "\n        .resumo.erro { background: #ffebee; border-left-color: #f44336; }"
            "\n        table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }"
            "\n        th { background: #3498db; color: white; padding: 12px; text-align: left; font-weight: bold; }"
            "\n        td { padding: 10px; border: 1px solid #ddd; }"
            "\n        tr:nth-child(even) { background: #f9f9f9; }"
            "\n        tr:hover { background: #f0f0f0; }"
            "\n        .status-ok { color: #4caf50; font-weight: bold; font-size: 18px; }"
            "\n        .status-alerta { color: #ff9800; font-weight: bold; font-size: 18px; }"
            "\n        .status-erro { color: #f44336; font-weight: bold; font-size: 18px; }"
            "\n        .secao-cadastro th { background: #2196f3; }"
            "\n        .secao-tecnico th { background: #009688; }"
            "\n        .secao-vertices th { background: #673ab7; }"
            "\n        .secao-confrontantes th { background: #ff5722; }"
            "\n        .secao-erros { background: #ffebee; padding: 15px; border-left: 5px solid #f44336; margin: 20px 0; }"
            "\n        .secao-alertas { background: #fff3e0; padding: 15px; border-left: 5px solid #ff9800; margin: 20px 0; }"
            "\n        .secao-ok { background: #e8f5e9; padding: 15px; border-left: 5px solid #4caf50; margin: 20px 0; }"
            "\n        .parecer { padding: 20px; margin: 20px 0; border: 3px solid; font-size: 16px; font-weight: bold; }"
            "\n        .parecer-aprovado { background: #e8f5e9; border-color: #4caf50; color: #2e7d32; }"
            "\n        .parecer-ressalvas { background: #fff3e0; border-color: #ff9800; color: #e65100; }"
            "\n        .parecer-reprovado { background: #ffebee; border-color: #f44336; color: #c62828; }"
            "\n        .legenda { background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }"
            "\n        .analise { font-style: italic; color: #555; margin: 10px 0; padding: 10px; background: #f9f9f9; }"
            "\n    </style>"
            "\n</head>"
            "\n<body>"
            "\n<div class='container'>"
            "\n"
            "\n<!-- SEÇÃO 1: DADOS CADASTRAIS -->"
            "\n<h2>📋 1. DADOS CADASTRAIS</h2>"
            "\n<table class='secao-cadastro'>"
            "\n<thead>"
            "\n    <tr>"
            "\n        <th>DADO</th>"
            "\n        [COLUNAS DOS DOCUMENTOS FORNECIDOS]"
            "\n        <th style='text-align:center;'>STATUS</th>"
            "\n    </tr>"
            "\n</thead>"
            "\n<tbody>"
            "\n    <tr>"
            "\n        <td><strong>Proprietário(s)</strong></td>"
            "\n        [DADOS DE CADA DOCUMENTO]"
            "\n        <td style='text-align:center;'><span class='status-ok'>✅</span></td>"
            "\n    </tr>"
            "\n    <!-- Repetir para: Nome do Imóvel, Matrícula(s), Município, UF, Código INCRA, etc -->"
            "\n    <tr>"
            "\n        <td><strong>UF</strong></td>"
            "\n        <td>[extrair]</td>"
            "\n        <td>[extrair]</td>"
            "\n        <td>[extrair/N/A]</td>"
            "\n        <td style='text-align:center;'><span class='status-ok'>✅</span></td>"
            "\n    </tr>"
            "\n    <tr>"
            "\n        <td><strong>Código INCRA</strong></td>"
            "\n        <td>[extrair]</td>"
            "\n        <td>[extrair]</td>"
            "\n        <td>[extrair/N/A]</td>"
            "\n        <td style='text-align:center;'><span class='status-ok'>✅</span></td>"
            "\n    </tr>"
            "\n    <tr>"
            "\n        <td><strong>CCIR</strong></td>"
            "\n        <td>[extrair]</td>"
            "\n        <td>[extrair]</td>"
            "\n        <td>[extrair/N/A]</td>"
            "\n        <td style='text-align:center;'><span class='status-ok'>✅</span></td>"
            "\n    </tr>"
            "\n</tbody>"
            "\n</table>"
            "\n<p class='analise'><strong>Análise:</strong> [Breve comentário sobre consistência destes dados]</p>"
            "\n"
            "\n<!-- SEÇÃO 2: DADOS TÉCNICOS -->"
            "\n<h2>📐 2. DADOS TÉCNICOS/MENSURAÇÕES</h2>"
            "\n<table class='secao-tecnico'>"
            "\n<thead>"
            "\n    <tr>"
            "\n        <th>DADO</th>"
            "\n        <th>INCRA</th>"
            "\n        <th>MEMORIAL</th>"
            "\n        <th>PROJETO</th>"
            "\n        <th style='text-align:center;'>STATUS</th>"
            "\n    </tr>"
            "\n</thead>"
            "\n<tbody>"
            "\n    <tr>"
            "\n        <td><strong>Área Total (ha)</strong></td>"
            "\n        <td>[X,XXXX]</td>"
            "\n        <td>[X,XXXX]</td>"
            "\n        <td>[X,XXXX/N/A]</td>"
            "\n        <td style='text-align:center;'><span class='status-ok'>✅</span></td>"
            "\n    </tr>"
            "\n    <tr>"
            "\n        <td><strong>Perímetro (m)</strong></td>"
            "\n        <td>[X.XXX,XX]</td>"
            "\n        <td>[X.XXX,XX]</td>"
            "\n        <td>[X.XXX,XX/N/A]</td>"
            "\n        <td style='text-align:center;'><span class='status-ok'>✅</span></td>"
            "\n    </tr>"
            "\n    <tr>"
            "\n        <td><strong>Sistema Coordenadas</strong></td>"
            "\n        <td>[UTM/GEO]</td>"
            "\n        <td>[UTM/GEO]</td>"
            "\n        <td>[UTM/GEO/N/A]</td>"
            "\n        <td style='text-align:center;'><span class='status-ok'>✅</span></td>"
            "\n    </tr>"
            "\n    <tr>"
            "\n        <td><strong>Datum</strong></td>"
            "\n        <td>[SIRGAS]</td>"
            "\n        <td>[SIRGAS]</td>"
            "\n        <td>[SIRGAS/N/A]</td>"
            "\n        <td style='text-align:center;'><span class='status-ok'>✅</span></td>"
            "\n    </tr>"
            "\n    <tr>"
            "\n        <td><strong>Fuso</strong></td>"
            "\n        <td>[22/23]</td>"
            "\n        <td>[22/23]</td>"
            "\n        <td>[22/23/N/A]</td>"
            "\n        <td style='text-align:center;'><span class='status-ok'>✅</span></td>"
            "\n    </tr>"
            "\n</tbody>"
            "\n</table>"
            "\n<p class='analise'><strong>Análise:</strong> [Breve comentário sobre consistência destes dados]</p>"
            "\n"
            "\n<!-- SEÇÃO 3: VÉRTICES -->"
            "\n<h2>🗺️ 3. COORDENADAS DOS VÉRTICES</h2>"
            "\n<table class='secao-vertices'>"
            "\n<thead>"
            "\n    <tr>"
            "\n        <th>VÉRTICE</th>"
            "\n        <th>INCRA (Coordenadas)</th>"
            "\n        <th>MEMORIAL (Coordenadas)</th>"
            "\n        <th>PROJETO (Coordenadas)</th>"
            "\n        <th style='text-align:center;'>STATUS</th>"
            "\n    </tr>"
            "\n</thead>"
            "\n<tbody>"
            "\n    <tr>"
            "\n        <td><strong>V1</strong></td>"
            "\n        <td>[E=XXX N=YYY]</td>"
            "\n        <td>[E=XXX N=YYY]</td>"
            "\n        <td>[E=XXX N=YYY/N/A]</td>"
            "\n        <td style='text-align:center;'><span class='status-ok'>✅</span></td>"
            "\n    </tr>"
            "\n    <!-- ADICIONE UMA LINHA PARA CADA VÉRTICE (V2, V3, V4... até o último!) -->"
            "\n    <!-- NÃO OMITA NENHUM VÉRTICE! -->"
            "\n</tbody>"
            "\n</table>"
            "\n<p class='analise'><strong>Análise:</strong> [Comentário sobre consistência das coordenadas]</p>"
            "\n"
            "\n<!-- SEÇÃO 4: SEGMENTO VANTE -->"
            "\n<h2>📐 4. SEGMENTO VANTE</h2>"
            "\n<table class='secao-vertices'>"
            "\n<thead>"
            "\n    <tr>"
            "\n        <th>SEGMENTO</th>"
            "\n        <th>INCRA (Azimute/Dist./Confrontações)</th>"
            "\n        <th>PROJETO (Azimute/Dist.)</th>"
            "\n        <th style='text-align:center;'>STATUS</th>"
            "\n    </tr>"
            "\n</thead>"
            "\n<tbody>"
            "\n    <tr>"
            "\n        <td><strong>S1</strong></td>"
            "\n        <td>[Az=XXX° Dist=YY.YYm Conf=...]</td>"
            "\n        <td>[Az=XXX° Dist=YY.YYm]</td>"
            "\n        <td style='text-align:center;'><span class='status-ok'>✅</span></td>"
            "\n    </tr>"
            "\n    <!-- ADICIONE UMA LINHA PARA CADA SEGMENTO VANTE (S2, S3, S4... até o último!) -->"
            "\n    <!-- NÃO OMITA NENHUM SEGMENTO! -->"
            "\n</tbody>"
            "\n</table>"
            "\n<p class='analise'><strong>Análise:</strong> [Comentário sobre consistência dos segmentos vante]</p>"
            "\n"
            "\n<!-- LEGENDA -->"
            "\n<div class='legenda'>"
            "\n    <h3>LEGENDA DE STATUS</h3>"
            "\n    <p><span class='status-ok'>✅</span> = Dados idênticos e corretos</p>"
            "\n    <p><span class='status-alerta'>⚠️</span> = Pequena diferença (revisar, mas não bloqueia)</p>"
            "\n    <p><span class='status-erro'>❌</span> = Erro grave (correção obrigatória)</p>"
            "\n</div>"
            "\n"
            "\n<hr>"
            "\n<p style='text-align:center; color:#888; margin-top:30px;'><em>Relatório gerado por IA - Verificação humana sempre recomendada</em></p>"
            "\n"
            "\n</div>"
            "\n</body>"
            "\n</html>"
            "\n```"
            "\n"
            "\n⚠️ LEMBRE-SE:"
            "\n- Use <span class='status-ok'>✅</span> para dados corretos"
            "\n- Use <span class='status-alerta'>⚠️</span> para pequenas diferenças"
            "\n- Use <span class='status-erro'>❌</span> para erros graves"
            "\n- Liste TODOS os vértices encontrados na tabela de coordenadas"
            "\n- Liste TODOS os segmentos vante encontrados"
            "\n- Compare INCRA x PROJETO em todas as seções"
        )

        prompt.append(instrucoes_saida)
        return prompt
    def _extrair_html_puro(self, texto: str) -> str:
        """
        Extrai apenas o código HTML da resposta da IA, removendo texto extra.

        Args:
            texto: Resposta completa da IA

        Returns:
            HTML limpo sem texto antes ou depois
        """
        import re

        # Remover blocos de código markdown se houver
        texto = re.sub(r'```html\s*', '', texto)
        texto = re.sub(r'```\s*', '', texto)

        # Procurar pelo início do HTML de forma mais agressiva
        inicio_html = texto.find('<!DOCTYPE html>')
        if inicio_html == -1:
            inicio_html = texto.find('<!DOCTYPE HTML>')
        if inicio_html == -1:
            inicio_html = texto.find('<html')
        if inicio_html == -1:
            inicio_html = texto.find('<HTML')

        # Procurar pelo fim do HTML
        fim_html = texto.rfind('</html>')
        if fim_html == -1:
            fim_html = texto.rfind('</HTML>')

        if inicio_html != -1 and fim_html != -1:
            # Extrair apenas o HTML, cortando TODO o texto antes e depois
            html_puro = texto[inicio_html:fim_html + 7]  # +7 para incluir </html>

            # Limpar qualquer texto que ainda esteja antes do DOCTYPE
            # (remover linhas antes que não sejam HTML)
            linhas = html_puro.split('\n')
            primeira_linha_html = 0
            for i, linha in enumerate(linhas):
                if '<!DOCTYPE' in linha or '<html' in linha or '<HTML' in linha:
                    primeira_linha_html = i
                    break

            html_puro = '\n'.join(linhas[primeira_linha_html:])
            return html_puro
        else:
            # Se não encontrar marcadores HTML, retornar o texto original
            return texto

    def _executar_analise_gemini(self):
        """
        Executa a análise completa usando a API do Gemini.
        Deve ser executado em thread separada para não travar a GUI.
        """
        try:
            # Limpar área de resultados
            self.resultado_text.delete(1.0, tk.END)
            self.resultado_text.insert(tk.END, "🔄 Processando documentos...\n\n")

            # Carregar INCRA (com rotação)
            self._atualizar_status("Carregando INCRA...")
            self.incra_images = self._carregar_pdf_como_imagens(
                self.incra_path.get(),
                rotacionar_90=True
            )
            self.resultado_text.insert(
                tk.END,
                f"✅ INCRA carregado: {len(self.incra_images)} página(s)\n"
            )

            # Carregar Projeto
            self._atualizar_status("Carregando Projeto/Planta...")
            self.projeto_images = self._carregar_pdf_como_imagens(
                self.projeto_path.get()
            )
            self.resultado_text.insert(
                tk.END,
                f"✅ Projeto carregado: {len(self.projeto_images)} página(s)\n"
            )

            self.resultado_text.insert(tk.END, "\n" + "="*80 + "\n\n")

            # Configurar API do Gemini
            self._atualizar_status("Configurando API do Gemini...")
            genai.configure(api_key=self.api_key.get().strip())

            # Usar modelo Gemini 2.5 Flash Lite conforme especificado
            model = genai.GenerativeModel('gemini-2.0-flash-exp')

            # Construir prompt
            self._atualizar_status("Construindo análise multimodal...")
            prompt = self._construir_prompt_gemini()
            
            # Executar análise
            self._atualizar_status("Analisando documentos com IA... (pode levar alguns minutos)")
            self.resultado_text.insert(tk.END, "🤖 Gemini AI analisando os documentos...\n\n")
            self.root.update_idletasks()
            
            response = model.generate_content(prompt)

            # Limpar resposta - extrair apenas o HTML puro
            html_limpo = self._extrair_html_puro(response.text)

            # Exibir resultado
            self.resultado_text.insert(tk.END, html_limpo)

            # Salvar HTML para poder exportar depois
            self.ultimo_relatorio_html = html_limpo
            
            # Habilitar botão de salvar
            self.btn_salvar_html.config(state='normal')
            
            self._atualizar_status("✅ Análise concluída!")
            
            messagebox.showinfo("Sucesso", "Análise concluída com sucesso!\n\nVocê pode salvar o relatório em HTML clicando no botão abaixo.")
            
        except Exception as e:
            erro_msg = f"❌ ERRO: {str(e)}"
            self.resultado_text.insert(tk.END, f"\n\n{erro_msg}\n")
            self._atualizar_status("Erro na análise")
            messagebox.showerror("Erro", f"Ocorreu um erro durante a análise:\n\n{str(e)}")
            
        finally:
            self._habilitar_botoes()
            
    def _comparar_documentos(self):
        """Compara INCRA vs. Projeto."""
        if not self._validar_entrada():
            return

        self._desabilitar_botoes()

        # Executar em thread separada para não travar a GUI
        thread = threading.Thread(target=self._executar_analise_gemini)
        thread.daemon = True
        thread.start()


class JanelaComparacaoManual:
    """Janela para comparação visual manual dos documentos PDF."""

    def __init__(self, parent, incra_path, projeto_path):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Comparação Visual Manual - Georreferenciamento")
        self.janela.geometry("1400x900")
        self.janela.configure(bg='#2c3e50')

        # Caminhos dos arquivos
        self.incra_path = incra_path
        self.projeto_path = projeto_path

        # Listas de imagens carregadas
        self.incra_images = []
        self.projeto_images = []

        # Índices de página atual
        self.incra_pagina = 0
        self.projeto_pagina = 0

        # Níveis de zoom (100% = 1.0)
        self.incra_zoom = 1.0
        self.projeto_zoom = 1.0

        # Ângulo de rotação (0, 90, 180, 270)
        self.incra_rotacao = 0
        self.projeto_rotacao = 0

        # Posição do canvas (para arrastar)
        self.incra_pos_x = 0
        self.incra_pos_y = 0
        self.projeto_pos_x = 0
        self.projeto_pos_y = 0

        # Controle de arrastar
        self.incra_drag_start = None
        self.projeto_drag_start = None

        # Imagens PhotoImage (para exibição no Tkinter)
        self.incra_photo = None
        self.projeto_photo = None

        self._criar_interface()
        self._carregar_documentos()
        
    def _criar_interface(self):
        """Cria a interface da janela de comparação."""
        
        # Frame superior com título
        header_frame = tk.Frame(self.janela, bg='#34495e', height=60)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)
        
        titulo = tk.Label(
            header_frame,
            text="👁️  COMPARAÇÃO VISUAL MANUAL",
            font=('Arial', 18, 'bold'),
            bg='#34495e',
            fg='white'
        )
        titulo.pack(pady=15)
        
        # Frame principal com painéis
        main_frame = tk.Frame(self.janela, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Determinar quantos painéis criar
        num_paineis = 3 if self.projeto_path else 2
        
        # Criar painéis lado a lado
        if num_paineis == 2:
            # INCRA e Memorial
            self._criar_painel(main_frame, "INCRA", 0, 'incra')
            self._criar_painel(main_frame, "MEMORIAL", 1, 'memorial')
        else:
            # INCRA, Memorial e Projeto
            self._criar_painel(main_frame, "INCRA", 0, 'incra', largura_col=3)
            self._criar_painel(main_frame, "MEMORIAL", 1, 'memorial', largura_col=3)
            self._criar_painel(main_frame, "PROJETO", 2, 'projeto', largura_col=3)
        
        # Frame inferior com instruções
        footer_frame = tk.Frame(self.janela, bg='#34495e', height=50)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        footer_frame.pack_propagate(False)
        
        instrucoes = tk.Label(
            footer_frame,
            text="💡 Zoom: +/- ou Scroll Mouse | Páginas: ◀️ ▶️ | Girar: 🔄 90° | Arrastar: Segurar botão esquerdo",
            font=('Arial', 10),
            bg='#34495e',
            fg='#ecf0f1'
        )
        instrucoes.pack(pady=12)
        
    def _criar_painel(self, parent, titulo, coluna, tipo, largura_col=2):
        """Cria um painel de visualização para um documento."""
        
        # Frame do painel
        painel = tk.Frame(parent, bg='#ecf0f1', relief=tk.RAISED, borderwidth=2)
        painel.grid(row=0, column=coluna, sticky=(tk.N, tk.S, tk.E, tk.W), padx=5, pady=5)
        
        parent.columnconfigure(coluna, weight=1)
        parent.rowconfigure(0, weight=1)
        
        # Cabeçalho do painel
        header = tk.Frame(painel, bg='#3498db', height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"📄 {titulo}",
            font=('Arial', 14, 'bold'),
            bg='#3498db',
            fg='white'
        ).pack(pady=10)
        
        # Frame para canvas com scrollbar
        canvas_frame = tk.Frame(painel, bg='white')
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas para imagem
        canvas = tk.Canvas(canvas_frame, bg='white', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Salvar referência ao canvas
        setattr(self, f'{tipo}_canvas', canvas)
        
        # Configurar eventos do mouse para arrastar e zoom
        canvas.bind('<ButtonPress-1>', lambda e: self._iniciar_arrasto(tipo, e))
        canvas.bind('<B1-Motion>', lambda e: self._arrastar(tipo, e))
        canvas.bind('<ButtonRelease-1>', lambda e: self._finalizar_arrasto(tipo))
        canvas.bind('<MouseWheel>', lambda e: self._zoom_scroll(tipo, e))
        # Para Linux
        canvas.bind('<Button-4>', lambda e: self._zoom_scroll(tipo, e))
        canvas.bind('<Button-5>', lambda e: self._zoom_scroll(tipo, e))
        
        # Frame de controles
        controles = tk.Frame(painel, bg='#ecf0f1', height=120)
        controles.pack(fill=tk.X)
        controles.pack_propagate(False)
        
        # Linha 1: Navegação de páginas
        nav_frame = tk.Frame(controles, bg='#ecf0f1')
        nav_frame.pack(pady=5)
        
        btn_anterior = tk.Button(
            nav_frame,
            text="◀️ Anterior",
            command=lambda: self._mudar_pagina(tipo, -1),
            font=('Arial', 10),
            bg='#95a5a6',
            fg='white',
            relief=tk.RAISED,
            padx=10,
            pady=5
        )
        btn_anterior.pack(side=tk.LEFT, padx=5)
        
        # Label da página atual
        label_pagina = tk.Label(
            nav_frame,
            text="Página 1/1",
            font=('Arial', 10, 'bold'),
            bg='#ecf0f1'
        )
        label_pagina.pack(side=tk.LEFT, padx=10)
        setattr(self, f'{tipo}_label_pagina', label_pagina)
        
        btn_proximo = tk.Button(
            nav_frame,
            text="Próxima ▶️",
            command=lambda: self._mudar_pagina(tipo, 1),
            font=('Arial', 10),
            bg='#95a5a6',
            fg='white',
            relief=tk.RAISED,
            padx=10,
            pady=5
        )
        btn_proximo.pack(side=tk.LEFT, padx=5)
        
        # Linha 2: Controles de zoom
        zoom_frame = tk.Frame(controles, bg='#ecf0f1')
        zoom_frame.pack(pady=5)
        
        btn_zoom_out = tk.Button(
            zoom_frame,
            text="➖ Zoom -",
            command=lambda: self._ajustar_zoom(tipo, -0.2),
            font=('Arial', 10),
            bg='#e74c3c',
            fg='white',
            relief=tk.RAISED,
            padx=10,
            pady=5
        )
        btn_zoom_out.pack(side=tk.LEFT, padx=5)
        
        btn_zoom_reset = tk.Button(
            zoom_frame,
            text="🔄 Reset",
            command=lambda: self._resetar_zoom(tipo),
            font=('Arial', 10),
            bg='#95a5a6',
            fg='white',
            relief=tk.RAISED,
            padx=10,
            pady=5
        )
        btn_zoom_reset.pack(side=tk.LEFT, padx=5)
        
        btn_zoom_in = tk.Button(
            zoom_frame,
            text="➕ Zoom +",
            command=lambda: self._ajustar_zoom(tipo, 0.2),
            font=('Arial', 10),
            bg='#27ae60',
            fg='white',
            relief=tk.RAISED,
            padx=10,
            pady=5
        )
        btn_zoom_in.pack(side=tk.LEFT, padx=5)
        
        # Label do zoom atual
        label_zoom = tk.Label(
            zoom_frame,
            text="100%",
            font=('Arial', 10),
            bg='#ecf0f1'
        )
        label_zoom.pack(side=tk.LEFT, padx=10)
        setattr(self, f'{tipo}_label_zoom', label_zoom)
        
        # Linha 3: Controles de rotação
        rotacao_frame = tk.Frame(controles, bg='#ecf0f1')
        rotacao_frame.pack(pady=5)
        
        btn_girar = tk.Button(
            rotacao_frame,
            text="🔄 Girar 90°",
            command=lambda: self._girar_imagem(tipo),
            font=('Arial', 10),
            bg='#3498db',
            fg='white',
            relief=tk.RAISED,
            padx=10,
            pady=5
        )
        btn_girar.pack(side=tk.LEFT, padx=5)
        
        btn_resetar_rotacao = tk.Button(
            rotacao_frame,
            text="↻ Reset Rotação",
            command=lambda: self._resetar_rotacao(tipo),
            font=('Arial', 10),
            bg='#9b59b6',
            fg='white',
            relief=tk.RAISED,
            padx=10,
            pady=5
        )
        btn_resetar_rotacao.pack(side=tk.LEFT, padx=5)
        
        # Label da rotação atual
        label_rotacao = tk.Label(
            rotacao_frame,
            text="0°",
            font=('Arial', 10),
            bg='#ecf0f1'
        )
        label_rotacao.pack(side=tk.LEFT, padx=10)
        setattr(self, f'{tipo}_label_rotacao', label_rotacao)
        
    def _carregar_documentos(self):
        """Carrega os documentos PDF como imagens."""
        try:
            # Criar diálogo de progresso
            progress = tk.Toplevel(self.janela)
            progress.title("Carregando...")
            progress.geometry("400x150")
            progress.transient(self.janela)
            progress.grab_set()
            
            tk.Label(
                progress,
                text="⏳ Carregando documentos...",
                font=('Arial', 12, 'bold')
            ).pack(pady=20)
            
            status_label = tk.Label(progress, text="", font=('Arial', 10))
            status_label.pack(pady=10)
            
            progress.update()
            
            # Carregar INCRA (com rotação)
            status_label.config(text="Carregando INCRA...")
            progress.update()
            self.incra_images = convert_from_path(self.incra_path, dpi=150)
            # Rotacionar INCRA
            self.incra_images = [img.rotate(-90, expand=True) for img in self.incra_images]

            # Carregar Projeto
            status_label.config(text="Carregando Projeto...")
            progress.update()
            self.projeto_images = convert_from_path(self.projeto_path, dpi=150)
            
            progress.destroy()
            
            # Exibir primeira página de cada documento
            self._exibir_pagina('incra')
            self._exibir_pagina('memorial')
            if self.projeto_path:
                self._exibir_pagina('projeto')
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar documentos:\n{str(e)}")
            self.janela.destroy()
            
    def _exibir_pagina(self, tipo):
        """Exibe a página atual de um documento."""
        # Obter lista de imagens e índice atual
        images = getattr(self, f'{tipo}_images')
        pagina = getattr(self, f'{tipo}_pagina')
        zoom = getattr(self, f'{tipo}_zoom')
        rotacao = getattr(self, f'{tipo}_rotacao')
        pos_x = getattr(self, f'{tipo}_pos_x')
        pos_y = getattr(self, f'{tipo}_pos_y')
        canvas = getattr(self, f'{tipo}_canvas')
        
        if not images or pagina >= len(images):
            return
            
        # Obter imagem original
        img_original = images[pagina].copy()
        
        # Aplicar rotação (se houver)
        if rotacao != 0:
            img_original = img_original.rotate(-rotacao, expand=True)
        
        # Aplicar zoom
        largura = int(img_original.width * zoom)
        altura = int(img_original.height * zoom)
        img_zoom = img_original.resize((largura, altura), Image.Resampling.LANCZOS)
        
        # Converter para PhotoImage
        photo = ImageTk.PhotoImage(img_zoom)
        setattr(self, f'{tipo}_photo', photo)  # Manter referência
        
        # Limpar canvas e exibir imagem
        canvas.delete("all")
        canvas.create_image(pos_x, pos_y, anchor=tk.NW, image=photo, tags='imagem')
        canvas.config(scrollregion=canvas.bbox("all"))
        
        # Atualizar label de página
        label_pagina = getattr(self, f'{tipo}_label_pagina')
        label_pagina.config(text=f"Página {pagina + 1}/{len(images)}")
        
        # Atualizar label de zoom
        label_zoom = getattr(self, f'{tipo}_label_zoom')
        label_zoom.config(text=f"{int(zoom * 100)}%")
        
        # Atualizar label de rotação
        label_rotacao = getattr(self, f'{tipo}_label_rotacao')
        label_rotacao.config(text=f"{rotacao}°")
        
    def _mudar_pagina(self, tipo, direcao):
        """Muda para página anterior ou próxima."""
        images = getattr(self, f'{tipo}_images')
        pagina_atual = getattr(self, f'{tipo}_pagina')
        
        nova_pagina = pagina_atual + direcao
        
        # Verificar limites
        if 0 <= nova_pagina < len(images):
            setattr(self, f'{tipo}_pagina', nova_pagina)
            self._exibir_pagina(tipo)
            
    def _ajustar_zoom(self, tipo, delta):
        """Ajusta o nível de zoom."""
        zoom_atual = getattr(self, f'{tipo}_zoom')
        novo_zoom = max(0.2, min(3.0, zoom_atual + delta))  # Limitar entre 20% e 300%
        
        setattr(self, f'{tipo}_zoom', novo_zoom)
        self._exibir_pagina(tipo)
        
    def _resetar_zoom(self, tipo):
        """Reseta o zoom para 100%."""
        setattr(self, f'{tipo}_zoom', 1.0)
        self._exibir_pagina(tipo)
    
    def _girar_imagem(self, tipo):
        """Gira a imagem em 90 graus no sentido horário."""
        rotacao_atual = getattr(self, f'{tipo}_rotacao')
        nova_rotacao = (rotacao_atual + 90) % 360
        setattr(self, f'{tipo}_rotacao', nova_rotacao)
        
        # Resetar posição ao girar
        setattr(self, f'{tipo}_pos_x', 0)
        setattr(self, f'{tipo}_pos_y', 0)
        
        self._exibir_pagina(tipo)
    
    def _resetar_rotacao(self, tipo):
        """Reseta a rotação para 0 graus."""
        setattr(self, f'{tipo}_rotacao', 0)
        setattr(self, f'{tipo}_pos_x', 0)
        setattr(self, f'{tipo}_pos_y', 0)
        self._exibir_pagina(tipo)
    
    def _iniciar_arrasto(self, tipo, event):
        """Inicia o arrasto da imagem."""
        canvas = getattr(self, f'{tipo}_canvas')
        canvas.config(cursor="fleur")  # Cursor de mover
        setattr(self, f'{tipo}_drag_start', (event.x, event.y))
    
    def _arrastar(self, tipo, event):
        """Arrasta a imagem."""
        drag_start = getattr(self, f'{tipo}_drag_start')
        if drag_start is None:
            return
        
        # Calcular deslocamento
        dx = event.x - drag_start[0]
        dy = event.y - drag_start[1]
        
        # Atualizar posição
        pos_x = getattr(self, f'{tipo}_pos_x')
        pos_y = getattr(self, f'{tipo}_pos_y')
        
        setattr(self, f'{tipo}_pos_x', pos_x + dx)
        setattr(self, f'{tipo}_pos_y', pos_y + dy)
        
        # Atualizar ponto de início
        setattr(self, f'{tipo}_drag_start', (event.x, event.y))
        
        # Redesenhar
        self._exibir_pagina(tipo)
    
    def _finalizar_arrasto(self, tipo):
        """Finaliza o arrasto da imagem."""
        canvas = getattr(self, f'{tipo}_canvas')
        canvas.config(cursor="")  # Cursor normal
        setattr(self, f'{tipo}_drag_start', None)
    
    def _zoom_scroll(self, tipo, event):
        """Ajusta o zoom com o scroll do mouse."""
        # Determinar direção do scroll
        if event.num == 4 or event.delta > 0:
            # Scroll para cima = zoom in
            delta = 0.1
        elif event.num == 5 or event.delta < 0:
            # Scroll para baixo = zoom out
            delta = -0.1
        else:
            return
        
        # Ajustar zoom
        zoom_atual = getattr(self, f'{tipo}_zoom')
        novo_zoom = max(0.2, min(5.0, zoom_atual + delta))  # Limitar entre 20% e 500%
        
        setattr(self, f'{tipo}_zoom', novo_zoom)
        self._exibir_pagina(tipo)


def main():
    """Função principal para iniciar a aplicação."""
    root = tk.Tk()
    app = VerificadorGeorreferenciamento(root)
    root.mainloop()


if __name__ == "__main__":
    main()