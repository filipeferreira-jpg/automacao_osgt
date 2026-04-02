"""
Módulo de automação usando OCR (Tesseract)
Encontra textos na tela e clica neles
"""

import cv2
import re
import win32com.client
import pyautogui
import pytesseract
import time
import pyperclip
from datetime import datetime
import numpy as np
from collections import Counter
from difflib import SequenceMatcher
from PIL import Image, ImageDraw, ImageOps, ImageEnhance
from models.captura_tela import CapturaTela

# Configuração do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class AutomacaoOCR:
    """Automação inteligente usando OCR para localizar elementos"""

    def __init__(self, titulo_janela=None):
        self.captura = CapturaTela()
        self.cache_ocr = {}  # Cache dos textos detectados

        if titulo_janela:
            self.captura.encontrar_janela(titulo_janela)
            self.captura.focar_janela()
            
    def _similaridade(self, texto_a, texto_b):
        """Retorna % de similaridade entre dois textos (0.0 a 1.0)
        Exemplos:
            'Faturas' x 'Faturas'  → 1.0  (100%)
            'Faluras' x 'Faturas'  → 0.86 ( 86%)
            'Fatura'  x 'Faturas'  → 0.92 ( 92%)
        """
        return SequenceMatcher(
            None,
            texto_a.strip().lower(),
            texto_b.strip().lower()
        ).ratio()        

    def limpar_cache_ocr(self):
        """Limpa o cache de OCR"""
        self.cache_ocr = {}
        self.captura.limpar_cache()
        print("🗑️  Cache OCR limpo")
    # Dentro da classe AutomacaoOCR em automacao_cliques.py

    def processar_ocr(self, regiao=None, forcar_nova=False, preprocessing_config=None):
        """
        Processa OCR na janela ou região específica, com pré-processamento opcional.

        Args:
            regiao (tuple): (x, y, w, h) da região a capturar.
            forcar_nova (bool): Se True, força nova captura e OCR, ignorando o cache.
            preprocessing_config (dict): Dicionário com configurações de pré-processamento:
                - 'amplify_factor': Fator de ampliação (ex: 3 para 3x).
                - 'grayscale': True para converter para escala de cinza.
                - 'contrast': Fator de contraste (ex: 2.0 para 2x).
                - 'threshold': Limiar para binarização (0-255).
                - 'invert': True para inverter cores (útil para texto claro em fundo escuro).
                - 'whitelist': Caracteres permitidos para Tesseract (ex: '0123456789,.').
                - 'psm': Page Segmentation Mode para Tesseract (ex: 6 para linha única).
                - 'debug_filename_prefix': Prefixo para salvar arquivos de debug (ex: 'debug_qtde_ocr').

        Returns:
            dict: Dados do OCR, screenshot e região, ou None em caso de falha.
        """
        cache_key = str(regiao) + str(preprocessing_config) if regiao else 'full' + str(preprocessing_config)

        if not forcar_nova and cache_key in self.cache_ocr:
            print("📋 Usando OCR em cache")
            return self.cache_ocr[cache_key]

        print("🔍 Processando OCR...")

        if regiao:
            x, y, w, h = regiao
            screenshot = self.captura.capturar_regiao(x, y, w, h)
        else:
            screenshot = self.captura.capturar(forcar_nova=True)

        if not screenshot:
            return None

        img_processada = screenshot.copy()
        debug_prefix = preprocessing_config.get('debug_filename_prefix', 'debug_ocr') if preprocessing_config else 'debug_ocr'

        # Salva o screenshot original para debug, se houver pré-processamento
        if preprocessing_config:
            img_processada.save(f'{debug_prefix}_original.png')
            print(f"💾 Debug original salvo: '{debug_prefix}_original.png'")

            # Aplica pré-processamento se configurado
            #amplify_factor = 1
            amplify_factor = preprocessing_config.get('amplify_factor', 1)
            if amplify_factor > 1:
                img_processada = img_processada.resize(
                    (img_processada.width * amplify_factor, img_processada.height * amplify_factor),
                    Image.LANCZOS
                )

            if preprocessing_config.get('grayscale', False):
                img_processada = img_processada.convert('L')

            contrast_factor = preprocessing_config.get('contrast', 1.0)
            if contrast_factor != 1.0:
                enhancer = ImageEnhance.Contrast(img_processada)
                img_processada = enhancer.enhance(contrast_factor)

            threshold = preprocessing_config.get('threshold')
            if threshold is not None:
                #img_processada = img_processada.point(lambda p: p > threshold and 255)
                img_processada = img_processada.point(lambda p: 255 if p > threshold else 0)

            if preprocessing_config.get('invert', False):
                img_processada = ImageOps.invert(img_processada)

            img_processada.save(f'{debug_prefix}_processada.png')
            print(f"💾 Debug processado salvo: '{debug_prefix}_processada.png'")

        # Configuração do Tesseract
        config_tesseract = ''
        if preprocessing_config:
            if 'whitelist' in preprocessing_config:
                config_tesseract += f'-c tessedit_char_whitelist={preprocessing_config["whitelist"]} '
            if 'psm' in preprocessing_config:
                config_tesseract += f'--psm {preprocessing_config["psm"]}'

        data = pytesseract.image_to_data(
            img_processada,
            lang='por',
            config=config_tesseract.strip(),
            output_type=pytesseract.Output.DICT
        )

        self.cache_ocr[cache_key] = {
            'data': data,
            'regiao': regiao,
            'screenshot': screenshot # Guarda o original, não o processado
        }

        print(f"✓ OCR processado - {len(data['text'])} elementos detectados")
        return self.cache_ocr[cache_key]
    
    def encontrar_texto(self, texto_busca, confianca_minima=30, regiao=None, similaridade_minima=0.75, preprocessing_config=None):
        """Encontra texto na tela usando OCR com tolerância a erros de leitura e pré-processamento opcional"""

        resultado_ocr = self.processar_ocr(regiao=regiao, preprocessing_config=preprocessing_config)
        if not resultado_ocr:
            return None

        data = resultado_ocr['data']
        regiao_offset = resultado_ocr.get('regiao')
        melhor_resultado  = None
        melhor_similaridade = 0

        for i in range(len(data['text'])):
            texto = data['text'][i].strip()
            conf  = int(data['conf'][i])

            if not texto:
                continue

            sim = self._similaridade(texto, texto_busca)

            confianca_ok    = conf >= confianca_minima
            similaridade_ok = sim >= similaridade_minima

            if similaridade_ok and confianca_ok:
                if sim > melhor_similaridade:
                    melhor_similaridade = sim
                    
                    # teste padrozinação amplify_factor
                    amplify_factor = preprocessing_config.get('amplify_factor', 1) if preprocessing_config else 1
                    
                    x_rel = (data['left'][i] + data['width'][i] // 2) // amplify_factor
                    y_rel = (data['top'][i]  + data['height'][i] // 2) // amplify_factor

                    if regiao_offset: # Se a captura foi de uma região, ajusta as coordenadas
                        x_rel += regiao_offset[0]
                        y_rel += regiao_offset[1]

                    coords = self.captura.obter_posicao_absoluta(x_rel, y_rel)
                    if coords is None:
                        print("❌ Janela não encontrada, não foi possível obter coordenadas absolutas")
                        return None

                    x_abs, y_abs = coords

                    melhor_resultado = {
                        'texto'       : texto,
                        'confianca'   : conf,
                        'similaridade': round(sim * 100, 1),
                        'x_rel'       : x_rel,
                        'y_rel'       : y_rel,
                        'x_abs'       : x_abs,
                        'y_abs'       : y_abs,
                    }

        if melhor_resultado:
            print(f"✓ Encontrado: '{melhor_resultado['texto']}' "
                f"(confiança: {melhor_resultado['confianca']}%, "
                f"similaridade: {melhor_resultado['similaridade']}%)")
        else:
            print(f"❌ Texto '{texto_busca}' não encontrado")

        return melhor_resultado
    
    def clicar_em_texto(self, texto_busca, tipo_clique='single', pausar=1.0,
                        confianca_minima=30, regiao=None, tentativas=3,
                        similaridade_minima=0.75): 
        """Encontra um texto e clica nele"""
        for tentativa in range(1, tentativas + 1):
            self.limpar_cache_ocr()

            if tentativa > 1:
                print(f"🔄 Tentativa {tentativa}/{tentativas}...")
                time.sleep(1)

            resultado = self.encontrar_texto(
                texto_busca,
                confianca_minima=confianca_minima,
                regiao=regiao,
                similaridade_minima=similaridade_minima  # ✅ aqui estava faltando
            )

            if resultado:
                print(f"🖱️  Clicando em '{resultado['texto']}' - tipo: {tipo_clique}")

                if tipo_clique == 'double':
                    pyautogui.click(resultado['x_abs'], resultado['y_abs'])
                    time.sleep(0.1)
                    pyautogui.click(resultado['x_abs'], resultado['y_abs'])
                elif tipo_clique == 'right':
                    pyautogui.rightClick(resultado['x_abs'], resultado['y_abs'])
                else:  # single
                    pyautogui.click(resultado['x_abs'], resultado['y_abs'])

                time.sleep(pausar)
                self.limpar_cache_ocr()
                print("✓ Clique executado!")
                return True

        print(f"❌ Texto '{texto_busca}' não encontrado após {tentativas} tentativas.")
        return False

    def clicar_menu_modulos(self, nome_menu, pausar=0.5, confianca_minima=25, similaridade_minima=0.8, tentativas=3):
        """
        Na janela 'Módulos', clica no texto do menu desejado
        (ex.: 'Import', 'Broker', 'In Out') usando OCR.

        Args:
            nome_menu       : texto exato do menu a clicar (ex.: 'Import')
            pausar          : pausa após o clique
            confianca_minima: confiança mínima do OCR
            tentativas      : número de tentativas do OCR

        Returns:
            True se clicou com sucesso, False caso contrário

        Exemplo de uso:
            auto_ocr.clicar_menu_modulos('Import')
            auto_ocr.clicar_menu_modulos('Broker')
            auto_ocr.clicar_menu_modulos('In Out')
        """
        print(f"\n🧭 Clicando no módulo '{nome_menu}'...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela selecionada")
            return False

        # Região onde ficam os menus (painel esquerdo da janela Módulos)
        # Cobre a lista: Broker / Import / In Out
        regiao_lista = (50, 180, 260, 260)  # x_rel, y_rel, largura, altura

        sucesso = self.clicar_em_texto(
            texto_busca=nome_menu,
            tipo_clique='double',
            pausar=pausar,
            regiao=regiao_lista,
            confianca_minima=confianca_minima,
            similaridade_minima=0.80,
            tentativas=tentativas
        )

        if sucesso:
            print(f"✅ Menu '{nome_menu}' clicado com sucesso!")
        else:
            print(f"❌ Não foi possível clicar em '{nome_menu}' via OCR.")
            print(f"   Verifique se o texto '{nome_menu}' está visível na janela Módulos.")

        return sucesso
    
    def clicar_menu_barra(self, nome_menu, pausar=1.0):
        """Clica em menu da barra superior usando OCR"""
        print(f"\n📋 Clicando no menu: '{nome_menu}'")
        regiao_menu = (0, 0, self.captura.janela_atual.width, 50)
        return self.clicar_em_texto(nome_menu, tipo_clique='single', pausar=pausar, regiao=regiao_menu)
        
    def clicar_botao_toolbar(self, nome_botao, pausar=1.0, similaridade_minima=0.65):
        print(f"\n🔘 Clicando no botão: '{nome_botao}'")
        self.limpar_cache_ocr()

        regiao_toolbar = (0, 60, self.captura.janela_atual.width, 120)

        return self.clicar_em_texto(
            nome_botao,
            tipo_clique='single',
            pausar=pausar,
            regiao=regiao_toolbar,
            confianca_minima=0,          # ✅ ignora confiança pois OCR de ícones é ruim
            similaridade_minima=similaridade_minima,    # ✅ tolera erros de leitura como Faluras→Faturas
            tentativas=3
        )

    def aguardar_janela_interna(self, texto_titulo, timeout=10, intervalo=1):
        """Aguarda uma janela INTERNA (MDI) aparecer"""
        print(f"⏳ Aguardando janela interna '{texto_titulo}' aparecer...")

        inicio = time.time()
        while time.time() - inicio < timeout:
            self.limpar_cache_ocr()
            regiao_titulo = (200, 100, self.captura.janela_atual.width - 200, 100)
            resultado = self.encontrar_texto(texto_titulo, confianca_minima=25, regiao=regiao_titulo)

            if resultado:
                print(f"✓ Janela interna '{texto_titulo}' detectada!")
                return True

            time.sleep(intervalo)

        print(f"❌ Timeout: janela interna '{texto_titulo}' não apareceu em {timeout}s")
        return False

    def clicar_botao_mais_janela_interna(self, pausar=1.0):
        """Clica no botão + (Novo) em janelas internas MDI"""
        print("\n➕ Clicando no botão '+' da janela interna...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela selecionada")
            return False

        # MÉTODO 1: OCR
        print("🔍 Tentando localizar botão '+' via OCR...")
        regiao_toolbar_interna = (230, 130, 100, 50) #coordenadas backups para resolução 1366x768 - janela menor (REVER ESSA REGIAO)
        #regiao_toolbar_interna = (230, 130, 100, 50) #coordenadas backups para resolução 1920x1080 - janela maior
        resultado = self.encontrar_texto('+', confianca_minima=20, regiao=regiao_toolbar_interna)

        if resultado:
            print(f"✓ Botão '+' encontrado via OCR")
            pyautogui.click(resultado['x_abs'], resultado['y_abs'])
            time.sleep(pausar)
            self.limpar_cache_ocr()
            return True

        # MÉTODO 2: Coordenadas fixas
        print("⚠️  OCR não encontrou, usando coordenadas fixas...")
        #x_abs, y_abs = self.captura.obter_posicao_absoluta(263, 150) #coordenadas backups para resolução 1920x1080 - janela maior
        x_abs, y_abs = self.captura.obter_posicao_absoluta(263, 150) #coordenadas backups para resolução 1366x768 - janela menor
        print(f"🖱️  Clicando em ({x_abs}, {y_abs})...")
        pyautogui.click(x_abs, y_abs)
        time.sleep(pausar)
        self.limpar_cache_ocr()
        print("✓ Clique no botão '+' executado!")
        return True

    def clicar_menu_composicao_janela_interna(self, pausar=1.0):
        """
        Clica no menu COMPOSIÇÃO dentro da janela de fatura
        (após clicar no botão +)
        """
        print("\n📋 Clicando no menu COMPOSIÇÃO da janela interna...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela selecionada")
            return False

        # MÉTODO 1: Tentar OCR primeiro
        print("🔍 Tentando localizar menu 'COMPOSIÇÃO' via OCR...")

        # Procura em uma região mais ampla (toda a barra superior da janela MDI)
        regiao_toolbar_interna = (200, 120, 700, 80)

        resultado = self.encontrar_texto(
            'Composição',
            confianca_minima=20,
            regiao=regiao_toolbar_interna
        )

        if resultado:
            print(f"✓ Menu 'COMPOSIÇÃO' encontrado via OCR em ({resultado['x_abs']}, {resultado['y_abs']})")
            pyautogui.click(resultado['x_abs'], resultado['y_abs'])
            time.sleep(pausar)
            self.limpar_cache_ocr()
            return True

        # MÉTODO 2: Usar coordenadas fixas
        print("⚠️  OCR não encontrou, usando coordenadas fixas...")

        # Suas coordenadas: (601, 150) relativo à janela Import -  - coordenadas capturadas através do script 'mapear_multiplos_elementos.py'
        x_abs, y_abs = self.captura.obter_posicao_absoluta(601, 150)

        print(f"🖱️  Clicando em ({x_abs}, {y_abs})...")
        pyautogui.click(x_abs, y_abs)
        time.sleep(pausar)
        self.limpar_cache_ocr()

        print("✓ Clique no menu 'COMPOSIÇÃO' executado!")
        return True
    
    def clicar_mais_composicao_janela_interna(self, pausar=1.0):
        """
        Clica no menu COMPOSIÇÃO dentro da janela de fatura
        (após clicar no botão +)
        """
        print("\n📋 Clicando no menu COMPOSIÇÃO da janela interna...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela selecionada")
            return False
        
        # ESTE SUBMENU VAMOS CLICAR DIRETO NA COORDENADA, POIS NÃO TEM TEXTO VISÍVEL PARA O OCR DETECTAR (É SÓ UM ÍCONE DE ADIÇÃO MESMO)
        # Suas coordenadas: (1102, 208) relativo à janela Import - coordenadas capturadas através do script 'mapear_multiplos_elementos.py'
        x_abs, y_abs = self.captura.obter_posicao_absoluta(1102, 208)

        print(f"🖱️  Clicando em ({x_abs}, {y_abs})...")
        pyautogui.click(x_abs, y_abs)
        time.sleep(pausar)
        self.limpar_cache_ocr()

        print("✓ Clique no menu 'COMPOSIÇÃO' executado!")
        return True

    def listar_todos_textos(self, confianca_minima=30):
        """Lista TODOS os textos detectados na tela"""
        print("\n" + "="*60)
        print("📋 TODOS OS TEXTOS DETECTADOS:")
        print("="*60)

        resultado_ocr = self.processar_ocr(forcar_nova=True)
        if not resultado_ocr:
            return []

        data = resultado_ocr['data']
        textos = []

        for i in range(len(data['text'])):
            texto = data['text'][i].strip()
            conf = int(data['conf'][i])

            if texto and conf >= confianca_minima:
                textos.append({'texto': texto, 'confianca': conf})
                print(f"✓ '{texto}' (confiança: {conf}%)")

        print("="*60)
        print(f"Total: {len(textos)} textos")
        print("="*60 + "\n")

        return textos

    def listar_texto_regiao(self, confianca_minima=30, regiao=None):
        """Lista TODOS os textos detectados na tela"""
        print("\n" + "="*60)
        print("📋 TODOS OS TEXTOS DETECTADOS:")
        print("="*60)

        # força uma nova captura OCR (não usa cache)
        resultado_ocr = self.processar_ocr(forcar_nova=True, regiao=regiao)  # ✅ passa regiao
        if not resultado_ocr:
            return []

        data = resultado_ocr['data']
        textos = []

        for i in range(len(data['text'])):
            texto = data['text'][i].strip()
            conf  = int(data['conf'][i])

            if texto and conf >= confianca_minima:
                textos.append({'texto': texto, 'confianca': conf})
                print(f"✓ '{texto}' (confiança: {conf}%)")

        print("="*60)
        print(f"Total: {len(textos)} textos")
        print("="*60 + "\n")

        return textos
    
    def criar_mapa_visual(self, nome_arquivo='mapa_ocr.png'):
        """Cria imagem visual com retângulos em todos os textos detectados"""
        print("🎨 Criando mapa visual do OCR...")

        resultado_ocr = self.processar_ocr(forcar_nova=True)
        if not resultado_ocr:
            return False

        screenshot = resultado_ocr['screenshot'].copy()
        data = resultado_ocr['data']
        draw = ImageDraw.Draw(screenshot)

        for i in range(len(data['text'])):
            texto = data['text'][i].strip()
            conf = int(data['conf'][i])

            if texto and conf > 30:
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                draw.rectangle([(x, y), (x + w, y + h)], outline='red', width=2)
                try:
                    draw.text((x, y - 15), texto[:20], fill='red')
                except:
                    pass

        screenshot.save(nome_arquivo)
        print(f"✓ Mapa visual salvo: {nome_arquivo}")
        return True
    
    ### NOVAS CLASSES DE CLIQUES ESPECÍFICOS PARA ELEMENTOS DA JANELA DE FATURA (APÓS CLICAR NO BOTÃO +):
    def preencher_campo_num_ordem_filtro(self, numero_ordem, pausar=0.5):
        """
        Preenche o campo 'Núm. Ordem' do FILTRO (seção de busca)
        Usa coordenadas fixas e digita devagar para evitar duplicação

        Args:
            numero_ordem: Número da ordem a digitar
            pausar: Tempo de espera após preencher

        Returns:
            True se preencheu, False caso contrário
        """
        print(f"\n📋 Preenchendo campo 'Núm. Ordem' (filtro) com '{numero_ordem}'...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela selecionada")
            return False

        # Coordenadas do campo Núm. Ordem no filtro
        x_abs, y_abs = self.captura.obter_posicao_absoluta(342, 494)

        print(f"🖱️  Clicando no campo em ({x_abs}, {y_abs})...")
        pyautogui.click(x_abs, y_abs)
        time.sleep(0.5)  # Aguarda o campo focar

        # Limpa o campo
        print("🧹 Limpando campo...")
        # MÉTODO 1: Triple Click para selecionar tudo (mais confiável)
        pyautogui.click(x_abs, y_abs, clicks=2)  # 2 cliques = seleciona tudo
        time.sleep(0.3)
        pyautogui.press('delete')  # Apaga
        time.sleep(0.3)

        # Digita o número DEVAGAR (caractere por caractere com delay)
        print(f"⌨️  Digitando '{numero_ordem}' (devagar)...")
        numero_str = str(numero_ordem)

        # typewrite() ao invés de press() - MAIS CONFIÁVEL
        pyautogui.write(str(numero_ordem), interval=0.15)
        print(f"  ✓ Digitado: {numero_str}")
        time.sleep(pausar)

        self.limpar_cache_ocr()
        print(f"✓ Campo 'Núm. Ordem' (filtro) preenchido com '{numero_ordem}'!")
        return True

    def preencher_campo_part_number_filtro(self, part_number, pausar=0.5):
        """
        Preenche o campo 'Part Number' do FILTRO
        Usa coordenadas fixas e digita devagar

        Args:
            part_number: Part Number a digitar
            pausar: Tempo de espera após preencher

        Returns:
            True se preencheu, False caso contrário
        """
        print(f"\n📋 Preenchendo campo 'Part Number' (filtro) com '{part_number}'...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela selecionada")
            return False

        # Coordenadas do campo Part Number no filtro
        x_abs, y_abs = self.captura.obter_posicao_absoluta(714, 497)

        print(f"🖱️  Clicando no campo em ({x_abs}, {y_abs})...")
        pyautogui.click(x_abs, y_abs)
        time.sleep(0.5)

        # Limpa o campo
        print("🧹 Limpando campo...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.press('delete')
        time.sleep(0.3)

        # Digita o part number DEVAGAR
        print(f"⌨️  Digitando '{part_number}' (devagar)...")
        part_str = str(part_number)

        for i, char in enumerate(part_str):
            # Trata caracteres especiais
            if char == '-':
                pyautogui.press('minus')
            elif char == '_':
                pyautogui.press('underscore')
            elif char == '/':
                pyautogui.press('slash')
            else:
                pyautogui.press(char)

            time.sleep(0.15)  # Delay de 150ms entre cada caractere
            print(f"  ✓ Digitado: {char} ({i+1}/{len(part_str)})")

        time.sleep(pausar)

        self.limpar_cache_ocr()
        print(f"✓ Campo 'Part Number' (filtro) preenchido com '{part_number}'!")
        return True

    def preencher_campo_por_clipboard(self, x_rel, y_rel, valor, pausar=0.5):
        """
        Preenche campo usando área de transferência (clipboard)
        MÉTODO MAIS SEGURO - evita problemas com eventos de teclado

        Args:
            x_rel, y_rel: Coordenadas do campo
            valor: Valor a preencher
            pausar: Tempo de espera
        """
        print(f"\n📋 Preenchendo campo via clipboard com '{valor}'...")

        if not self.captura.janela_atual:
            return False

        x_abs, y_abs = self.captura.obter_posicao_absoluta(x_rel, y_rel)

        # 1. Clica no campo
        print(f"🖱️  Clicando no campo...")
        pyautogui.click(x_abs, y_abs)  # clica campo
        pyautogui.hotkey('ctrl', 'a') # Seleciona tudo
        time.sleep(0.3) # pequena pausa para garantir que o campo processou o Ctrl+A
        pyautogui.press('delete')  # Apaga
        time.sleep(0.3)

        # 2. Copia valor para clipboard
        print(f"📋 Copiando '{valor}' para clipboard...")
        pyperclip.copy(str(valor))
        time.sleep(0.2)

        # 3. Cola com Ctrl+V
        print(f"📋 Colando...")
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(pausar)

        self.limpar_cache_ocr()
        print(f"✓ Campo preenchido via clipboard!")
        return True
      
    def preencher_campo_clipboard(self, x_rel, y_rel, valor, pausar=0.5):
        valor_str = str(valor).strip()
        print(f"\n📋 Preenchendo campo via clipboard com '{valor_str}'...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela principal selecionada")
            return False

        x_abs, y_abs = self.captura.obter_posicao_absoluta(x_rel, y_rel)

        # 1. Reseta clipboard
        pyperclip.copy('')
        time.sleep(0.2)

        # 2. Foca no campo
        pyautogui.click(x_abs, y_abs)
        time.sleep(0.4)

        # 3. Limpa o campo
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.press('delete')
        time.sleep(0.2)

        # 4. Clica de novo para garantir foco
        pyautogui.click(x_abs, y_abs)
        time.sleep(0.3)

        # 5. Copia valor para clipboard
        pyperclip.copy(valor_str)
        time.sleep(0.4)

        # 6. ✅ Cola via win32com no lugar do pyautogui
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys("^v")
        time.sleep(pausar)

        self.limpar_cache_ocr()
        print(f"✓ Campo preenchido com '{valor_str}'!")
        return True

    def digitar_texto_devagar(self, texto, delay_entre_chars=0.15):
        """
        Digita texto caractere por caractere com delay
        Método genérico para usar em qualquer campo

        Args:
            texto: Texto a digitar
            delay_entre_chars: Delay em segundos entre cada caractere
        """
        print(f"⌨️  Digitando '{texto}' (devagar, delay={delay_entre_chars}s)...")
        texto_str = str(texto)

        for i, char in enumerate(texto_str):
            # Trata caracteres especiais
            if char == '-':
                pyautogui.press('minus')
            elif char == '_':
                pyautogui.press('underscore')
            elif char == '/':
                pyautogui.press('slash')
            elif char == '.':
                pyautogui.press('period')
            elif char == ',':
                pyautogui.press('comma')
            elif char == ' ':
                pyautogui.press('space')
            elif char.isdigit():
                pyautogui.press(char)
            elif char.isalpha():
                if char.isupper():
                    pyautogui.hotkey('shift', char.lower())
                else:
                    pyautogui.press(char)
            else:
                # Para outros caracteres, tenta escrever diretamente
                try:
                    pyautogui.write(char, interval=0)
                except:
                    print(f"  ⚠️  Caractere '{char}' ignorado")

            time.sleep(delay_entre_chars)

            # Mostra progresso a cada 5 caracteres
            if (i + 1) % 5 == 0 or (i + 1) == len(texto_str):
                print(f"  ✓ Progresso: {i+1}/{len(texto_str)} caracteres")

        print(f"✓ Texto '{texto}' digitado completamente!")
    
    def preencher_campo_por_coordenadas(self, x_rel, y_rel, valor, delay=0.15, 
                                    limpar_antes=True, pausar=0.5):
        """
        Preenche qualquer campo usando coordenadas e digitação lenta
        Método genérico reutilizável

        Args:
            x_rel, y_rel: Coordenadas relativas do campo
            valor: Valor a digitar
            delay: Delay entre caracteres (em segundos)
            limpar_antes: Se True, limpa o campo antes
            pausar: Tempo de espera após preencher

        Returns:
            True se preencheu, False caso contrário
        """
        print(f"\n📝 Preenchendo campo em ({x_rel}, {y_rel}) com '{valor}'...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela selecionada")
            return False

        # Converte para coordenadas absolutas
        x_abs, y_abs = self.captura.obter_posicao_absoluta(x_rel, y_rel)

        # Clica no campo
        print(f"🖱️  Clicando no campo...")
        pyautogui.click(x_abs, y_abs)
        time.sleep(0.5)

        # Limpa o campo se solicitado
        if limpar_antes:
            print("🧹 Limpando campo...")
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.2)
            pyautogui.press('delete')
            time.sleep(0.3)

        # Digita o valor usando o método devagar
        self.digitar_texto_devagar(valor, delay_entre_chars=delay)

        time.sleep(pausar)
        self.limpar_cache_ocr()

        print(f"✓ Campo preenchido com '{valor}'!")
        return True

    # FUNÇÃO TESTEE PARA O POPUP DE NENHUM ITEM ENCONTRADO - QUE APARECE APÓS CLICAR EM BUSCA COM FILTRO VAZIO
    def detectar_popup_nenhum_item(self, confianca_minima=10):
        """
        Verifica se o popup 'Nenhum item foi encontrado!' está visível.
        Região mapeada diretamente da imagem real do ONESOURCE.

        Returns:
            True  -> popup detectado
            False -> popup não encontrado
        """
        print("\n🔍 Verificando popup 'Nenhum item foi encontrado!'...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela principal selecionada")
            return False

        # Região exata do popup baseada na sua imagem:
        # O popup aparece aproximadamente entre:
        # x: 560, y: 290, largura: 240, altura: 130
        regiao_popup = (560, 290, 240, 130)

        # Força nova captura para pegar estado atual da tela
        self.limpar_cache_ocr()
        resultado_ocr = self.processar_ocr(regiao=regiao_popup, forcar_nova=True)

        if not resultado_ocr:
            print("❌ Falha ao capturar região do popup")
            return False

        data = resultado_ocr['data']

        # Textos alvo que identificam o popup
        textos_alvo = [
            'nenhum item foi encontrado',
            'nenhum item',
            'encontrado',
            'atenção'
        ]

        # Coleta todos os textos detectados na região
        textos_detectados = []
        for i in range(len(data['text'])):
            texto = data['text'][i].strip()
            if not texto:
                continue

            try:
                conf = int(data['conf'][i])
            except ValueError:
                conf = 0

            if conf < confianca_minima:
                continue

            textos_detectados.append(texto.lower())
            print(f"  📝 OCR detectou: '{texto}' (conf: {conf}%)")

        # Verifica se algum texto alvo foi encontrado
        texto_completo = ' '.join(textos_detectados)
        for alvo in textos_alvo:
            if alvo in texto_completo:
                print(f"✓ Popup detectado! Texto encontrado: '{alvo}'")
                return True

        print("❌ Popup não detectado na região mapeada")
        return False

    def fechar_popup_nenhum_item(self, pausar=1.0):
        """
        Fecha o popup 'Nenhum item foi encontrado!' clicando em OK.
        Tenta primeiro via OCR, depois fallback em coordenadas fixas.

        Returns:
            True  -> popup fechado com sucesso
            False -> popup não estava visível
        """
        print("\n🧩 Fechando popup 'Nenhum item foi encontrado!'...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela principal selecionada")
            return False

        # 1) Verifica se o popup está visível
        if not self.detectar_popup_nenhum_item():
            print("ℹ️  Popup não detectado, nada a fechar")
            return False

        # 2) Tenta clicar em 'OK' via OCR dentro da região do popup
        print("🖱️  Tentando clicar em 'OK' via OCR...")

        # Região aproximada do popup (na tela Import):
        # olhando o print, o popup fica mais ou menos no centro da janela.
        # Ajuste fino depois se quiser, mas isso já restringe bem a busca.
        # x, y, largura, altura
        #regiao_popup = (430, 210, 500, 330)
        regiao_popup = (560, 290, 240, 130)

        # Região menor focada no botão OK dentro do popup
        # (baseado no print: botão está na parte inferior do popup)
        regiao_ok = (620, 380, 140, 45)

        # Primeiro, tenta na região menor do botão OK
        self.limpar_cache_ocr()
        sucesso = self.clicar_em_texto(
            texto_busca='OK',
            tipo_clique='single',
            pausar=pausar,
            regiao=regiao_ok,
            confianca_minima=25,          # texto pequeno, confiança costuma ser baixa
            similaridade_minima=0.65,     # tolera variações: 0K, CK, etc.
            tentativas=2
        )

        if not sucesso:
            # Se não achou no recorte menor, tenta na região do popup inteiro
            print("⚠️  Não achou 'OK' na região do botão, tentando no popup inteiro...")
            self.limpar_cache_ocr()
            sucesso = self.clicar_em_texto(
                texto_busca='OK',
                tipo_clique='single',
                pausar=pausar,
                regiao=regiao_popup,
                confianca_minima=0,
                similaridade_minima=0.6,
                tentativas=2
            )

        if sucesso:
            print("✓ Popup fechado via OCR!")
            self.limpar_cache_ocr()
            return True

        # 3) Fallback: Coordenadas fixas
        print("⚠️  OCR não encontrou 'OK', usando coordenadas fixas...")

        # Essas coordenadas são relativas à janela Import; ajuste fino se necessário
        x_abs, y_abs = self.captura.obter_posicao_absoluta(680, 400)
        print(f"🖱️  Clicando em OK ({x_abs}, {y_abs})...")

        pyautogui.click(x_abs, y_abs)
        time.sleep(pausar)

        self.limpar_cache_ocr()
        print("✓ Popup fechado via coordenadas fixas!")
        return True

    # DEBUG PARA A FUNÇÃO DO ERRO DE NENHUM ITEM ENCONTRADO - PARA VER SE O OCR ESTÁ PEGANDO A REGIÃO CERTA DO POPUP
    def debug_popup_nenhum_item(self):
        """
        Salva screenshot da região do popup para debug.
        Use quando o OCR não estiver detectando corretamente.
        """
        print("\n🔍 DEBUG: Capturando região do popup...")

        if not self.captura.janela_atual:
            return

        # Captura região maior para ter certeza de pegar o popup inteiro
        regioes_teste = [
            (500, 270, 350, 180, 'debug_popup_regiao1.png'),
            (400, 200, 500, 300, 'debug_popup_regiao2.png'),
            (0,   0,   self.captura.janela_atual.width,
                    self.captura.janela_atual.height,
                    'debug_popup_tela_completa.png'),
        ]

        for x, y, w, h, nome in regioes_teste:
            screenshot = self.captura.capturar_regiao(x, y, w, h)
            if screenshot:
                screenshot.save(nome)
                print(f"  💾 Salvo: {nome} | Região: ({x}, {y}, {w}, {h})")

        print("✓ Abra os arquivos de debug para confirmar as coordenadas do popup")

    def ler_quantidades_grade(self, regiao_qtde, confianca_minima=8, preprocessing_config=None):
        """
        Lê todas as quantidades da coluna Qtde. e retorna lista de floats.
        Trata corretamente valores no formato BR, por exemplo:
        8.640,00000 -> 8640.0

        Estratégia:
        - OCR na região informada
        - captura tokens numéricos mesmo com ponto de milhar
        - agrupa por linha visual (campo 'top')
        - escolhe o melhor valor por linha
        """

        print("\n🔍 Lendo coluna 'Qtde.' da grade de resultados...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela selecionada")
            return []

        self.limpar_cache_ocr()

        resultado_ocr = self.processar_ocr(
            regiao=regiao_qtde,
            forcar_nova=True,
            preprocessing_config=preprocessing_config
        )

        if not resultado_ocr:
            print("❌ Falha ao processar OCR da coluna Qtde.")
            return []

        data = resultado_ocr['data']

        def normalizar_valor_ocr(texto):
            """
            Converte:
            '8.640,00000' -> 8640.0
            '640,00000'   -> 640.0
            '8640'        -> 8640.0
            """
            if not texto:
                return None

            texto = str(texto).strip()
            texto = re.sub(r'[^0-9.,]', '', texto)

            if not texto:
                return None

            # formato brasileiro com vírgula decimal
            if ',' in texto:
                texto = texto.replace('.', '').replace(',', '.')
            else:
                # se vier só com pontos, mantém apenas o último como decimal
                partes = texto.split('.')
                if len(partes) > 1:
                    texto = ''.join(partes[:-1]) + '.' + partes[-1]

            try:
                return float(texto)
            except ValueError:
                return None

        # aceita:
        # 8.640,00000
        # 640,00000
        # 8640
        padrao_numero = r'\d{1,3}(?:\.\d{3})*,\d+|\d+,\d+|\d+'

        candidatos = []

        print("\n📜 OCR bruto na coluna Qtde. (após pré-processamento):")
        for i in range(len(data['text'])):
            texto = str(data['text'][i]).strip()
            if not texto:
                continue

            try:
                conf = int(float(data['conf'][i]))
            except Exception:
                conf = 0

            top = int(data['top'][i]) if str(data['top'][i]).strip() else 0
            left = int(data['left'][i]) if str(data['left'][i]).strip() else 0

            print(f"  Texto='{texto}' | conf={conf}% | top={top}")

            if conf < confianca_minima:
                print(f"    ↳ descartado (conf {conf}% < mínimo {confianca_minima}%)")
                continue

            encontrados = re.findall(padrao_numero, texto)
            if not encontrados:
                print("    ↳ não contém padrão numérico válido")
                continue

            for trecho in encontrados:
                valor = normalizar_valor_ocr(trecho)
                if valor is None:
                    continue

                # evita lixo muito improvável
                if valor <= 0:
                    continue

                candidatos.append({
                    'valor': valor,
                    'texto': trecho,
                    'conf': conf,
                    'top': top,
                    'left': left
                })
                print(f"    ✓ candidato aceito: '{trecho}' -> {valor}")

        if not candidatos:
            print("❌ Nenhuma quantidade válida encontrada.")
            return []

        # Ordena visualmente por linha
        candidatos.sort(key=lambda x: (x['top'], x['left']))

        # Agrupa itens da mesma linha usando proximidade vertical
        grupos = []
        tolerancia_top = 18

        for item in candidatos:
            if not grupos:
                grupos.append([item])
                continue

            top_medio = sum(x['top'] for x in grupos[-1]) / len(grupos[-1])
            if abs(item['top'] - top_medio) <= tolerancia_top:
                grupos[-1].append(item)
            else:
                grupos.append([item])

        quantidades = []

        print("\n📋 Consolidação por linha:")
        for idx, grupo in enumerate(grupos, start=1):
            # escolhe o item de maior confiança; empate -> maior valor textual mais completo
            melhor = sorted(
                grupo,
                key=lambda x: (x['conf'], len(str(x['texto'])), x['left']),
                reverse=True
            )[0]

            quantidades.append(melhor['valor'])
            print(
                f"  Linha {idx}: valor={melhor['valor']} | "
                f"texto='{melhor['texto']}' | conf={melhor['conf']} | top={melhor['top']}"
            )

        print(f"\n✅ Quantidades extraídas: {quantidades}")
        return quantidades
    
    def _ler_e_processar_quantidades_grade(self, regiao_qtde, confianca_minima=10, preprocessing_config=None):
        """
        Função interna para ler as quantidades da grade usando ler_quantidades_grade.
        Retorna apenas a lista de quantidades lidas.
        """
        print("\n📊 Lendo e processando quantidades da grade...")
        quantidades_grade = self.ler_quantidades_grade(
            regiao_qtde=regiao_qtde,
            confianca_minima=confianca_minima,
            preprocessing_config=preprocessing_config
        )
        return quantidades_grade
    
    def ordenar_e_verificar_quantidade(self,
                                        x_qtde_header, y_qtde_header,
                                        quantidade_n8n,
                                        regiao_qtde, # Novo parâmetro
                                        tolerancia=0.01,
                                        confianca_minima_ocr=10,
                                        max_tentativas_ordenacao=2,
                                        preprocessing_config_qtde=None): # Novo parâmetro
        """
        Tenta ordenar a coluna 'Qtde.' e verifica se ALGUMA quantidade individual
        na grade é menor ou igual à quantidade esperada do N8N.
        Reordena se a primeira tentativa não for suficiente.

        Args:
            x_qtde_header, y_qtde_header: Coordenadas do cabeçalho da coluna 'Qtde.'.
            quantidade_n8n: Quantidade esperada do N8N.
            regiao_qtde: Região da coluna de quantidade para o OCR.
            tolerancia: Tolerância para a comparação de quantidades.
            confianca_minima_ocr: Confiança mínima para o OCR.
            max_tentativas_ordenacao: Número máximo de vezes para tentar ordenar a coluna.
            preprocessing_config_qtde: Configurações de pré-processamento para o OCR de quantidades.

        Returns:
            dict:
            {
                'bate': True/False,
                'quantidade_encontrada_grade': float (a primeira que bateu ou 0.0),
                'quantidade_n8n': float,
                'diferenca': float,
                'lista_grade': [floats...]
            }
        """
        print(f"\n🔄 Iniciando ordenação e verificação para quantidade N8N: {quantidade_n8n}")
        quantidade_n8n = self._to_float(quantidade_n8n)
        #quantidade_n8n = float(quantidade_n8n)
        quantidade_encontrada_grade = 0.0 # Inicializa com 0.0
        quantidades_grade = [] # Lista para armazenar as quantidades lidas da grade
        for tentativa_ordem in range(1, max_tentativas_ordenacao + 1):
            print(f"   Tentativa de ordenação {tentativa_ordem}/{max_tentativas_ordenacao}...")

            # Clica no cabeçalho da coluna "Qtde." para ordenar
            self.clicar_coordenadas_fixas(x_qtde_header, y_qtde_header, tipo_clique='double', pausar=0.7)
            time.sleep(1) # Pequena pausa para a ordenação ser aplicada visualmente

            # Lê as quantidades da grade usando a função interna
            quantidades_grade = self._ler_e_processar_quantidades_grade(
                regiao_qtde=regiao_qtde,
                confianca_minima=confianca_minima_ocr,
                preprocessing_config=preprocessing_config_qtde
            )

            if not quantidades_grade:
                print("⚠️  Nenhuma quantidade lida da grade após ordenação.")
                if tentativa_ordem < max_tentativas_ordenacao:
                    print("   Tentando reordenar a coluna...")
                    continue
                else:
                    print("   Máximo de tentativas de ordenação atingido sem ler quantidades.")
                    break # Sai do loop se não leu nada após todas as tentativas

            print(f"   Quantidades lidas da grade: {quantidades_grade}")

            # Lógica de comparação: verifica se ALGUMA quantidade lida é <= quantidade_n8n
            bate = False
            for qtde_lida in quantidades_grade:
                diferenca = abs(qtde_lida - quantidade_n8n)
                if qtde_lida <= quantidade_n8n + tolerancia: # Adiciona tolerância aqui também
                    print(f"   ✅ Remessa {qtde_lida} na grade é <= N8N {quantidade_n8n} (tolerância {tolerancia}).")
                    bate = True
                    quantidade_encontrada_grade = qtde_lida # Guarda a primeira que bateu
                    break # Encontrou uma que bateu, pode sair

            if bate:
                print(f"✅ Quantidade OK após ordenação (tentativa {tentativa_ordem}).")
                return {
                    'bate': True,
                    'quantidade_encontrada_grade': quantidade_encontrada_grade,
                    'quantidade_n8n': quantidade_n8n,
                    'diferenca': abs(quantidade_encontrada_grade - quantidade_n8n),
                    'lista_grade': quantidades_grade
                }
            else:
                print(f"❌ Nenhuma remessa na grade é igual ou menor que a quantidade N8N após ordenação (tentativa {tentativa_ordem}).")
                if tentativa_ordem < max_tentativas_ordenacao:
                    print("   Tentando reordenar a coluna...")
                else:
                    print("   Máximo de tentativas de ordenação atingido.")

        print("⚠️  Não foi possível validar a quantidade após todas as tentativas de ordenação.")
        # Retorna o último estado, mesmo que não tenha batido
        return {
            'bate': False,
            'quantidade_encontrada_grade': quantidade_encontrada_grade, # Pode ser 0.0 ou a última lida
            'quantidade_n8n': quantidade_n8n,
            'diferenca': abs(quantidade_encontrada_grade - quantidade_n8n),
            'lista_grade': quantidades_grade
        }
    
    def ordenar_e_verificar_saldo_maior_ou_igual_por_linhas(
        self,
        x_qtde_header, y_qtde_header,
        quantidade_n8n,
        regiao_qtde,
        tolerancia=0.01,
        confianca_minima_ocr=5,
        max_tentativas_ordenacao=3,
        preprocessing_config_qtde=None,
        altura_linha=18,
        margem_superior=0,
        margem_inferior=0
    ):
        q_n8n = self._to_float(quantidade_n8n)
        ultima_lista = []

        for tentativa in range(1, max_tentativas_ordenacao + 1):
            self.clicar_coordenadas_fixas(x_qtde_header, y_qtde_header, tipo_clique="double", pausar=0.7)
            time.sleep(1)

            lista_grade = self._ler_e_processar_quantidades_grade_por_linhas(
                regiao_qtde=regiao_qtde,
                confianca_minima=confianca_minima_ocr,
                preprocessing_config=preprocessing_config_qtde,
                altura_linha=altura_linha,
                margem_superior=margem_superior,
                margem_inferior=margem_inferior
            ) or []

            ultima_lista = lista_grade

            if not lista_grade:
                continue

            # ✅ saldo suficiente = existe algum valor >= solicitado
            for q in lista_grade:
                qf = self._to_float(q)
                if qf >= q_n8n - tolerancia:
                    return {
                        "bate": True,
                        "quantidade_encontrada_grade": qf,
                        "quantidade_n8n": q_n8n,
                        "lista_grade": lista_grade,
                        "tentativa": tentativa
                    }

        return {
            "bate": False,
            "quantidade_encontrada_grade": 0.0,
            "quantidade_n8n": self._to_float(quantidade_n8n),
            "lista_grade": ultima_lista
        }
        
    # Adicione este método dentro da classe AutomacaoOCR em automacao_cliques.py
    def aguardar_popup_informacao(self, timeout=60, intervalo=2, confianca_minima=15):
        """
        Aguarda até que o popup 'Informação' (com o botão OK) apareça na tela.
        Verifica a presença do texto 'Informação' ou 'OK' em uma região esperada do popup.

        Args:
            timeout: Tempo máximo de espera em segundos.
            intervalo: Intervalo entre as verificações em segundos.
            confianca_minima: Confiança mínima do OCR para considerar o texto detectado.

        Returns:
            True se o popup foi detectado, False caso contrário.
        """
        print(f"\n⏳ Aguardando popup 'Informação' aparecer (timeout: {timeout}s)...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela principal selecionada.")
            return False

        inicio = time.time()
        while time.time() - inicio < timeout:
            # Região aproximada do popup 'Informação' (centralizado na tela)
            # Baseado na imagem, o popup está centralizado.
            # x_rel, y_rel, largura, altura
            # Esta região deve cobrir o título 'Informação' e o botão 'OK'
            regiao_popup_info_detecao = (315, 315, 120, 150) # Coordenadas ajustadas para a detecção do popup

            self.limpar_cache_ocr() # Limpa o cache para forçar nova captura
            resultado_ocr = self.processar_ocr(regiao=regiao_popup_info_detecao, forcar_nova=True)

            if not resultado_ocr:
                print("❌ Falha ao capturar região do popup durante a espera.")
                time.sleep(intervalo)
                continue

            data = resultado_ocr['data']
            textos_detectados = []
            for i in range(len(data['text'])):
                texto = data['text'][i].strip()
                conf = int(data['conf'][i])
                if texto and conf >= confianca_minima:
                    textos_detectados.append(texto.lower())

            # Verifica se os textos 'informação' ou 'ok' estão presentes na região
            # Usamos 'informacao' e 'ok' para maior flexibilidade do OCR
            if 'informação' in ' '.join(textos_detectados) or 'informacao' in ' '.join(textos_detectados) or 'ok' in ' '.join(textos_detectados):
                print("✓ Popup 'Informação' detectado!")
                return True

            print(f"   Popup não detectado ainda. Tentando novamente em {intervalo}s...")
            time.sleep(intervalo)

        print(f"❌ Timeout: Popup 'Informação' não apareceu em {timeout}s.")
        return False
    
    def arrastar_coluna_quantidade(self, x_inicio_rel, y_inicio_rel, x_fim_rel, y_fim_rel, duracao_arraste=0.5, pausar=1.0):
        """
        Simula o clique e arraste para ajustar a largura de uma coluna na grade.
        Útil para aumentar o campo de visualização da coluna 'Quantidade'.

        Args:
            x_inicio_rel, y_inicio_rel: Coordenadas relativas do ponto de início do arraste (onde o clique é segurado).
            x_fim_rel, y_fim_rel: Coordenadas relativas do ponto final do arraste.
            duracao_arraste: Duração do movimento de arraste em segundos.
            pausar: Tempo de espera após o arraste.

        Returns:
            True se a operação foi executada, False se a janela não estiver focada.
        """
        print(f"\n↔️ Ajustando largura da coluna (arrastar de ({x_inicio_rel}, {y_inicio_rel}) para ({x_fim_rel}, {y_fim_rel}))...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela principal selecionada.")
            return False

        x_inicio_abs, y_inicio_abs = self.captura.obter_posicao_absoluta(x_inicio_rel, y_inicio_rel)
        x_fim_abs, y_fim_abs       = self.captura.obter_posicao_absoluta(x_fim_rel, y_fim_rel)

        print(f"🖱️  Clicando e arrastando de ({x_inicio_abs}, {y_inicio_abs}) para ({x_fim_abs}, {y_fim_abs})...")

        pyautogui.moveTo(x_inicio_abs, y_inicio_abs) # Move o mouse para o ponto inicial
        pyautogui.dragTo(x_fim_abs, y_fim_abs, duration=duracao_arraste, button='left') # Clica, segura e arrasta

        time.sleep(pausar)
        self.limpar_cache_ocr()
        print("✓ Arraste da coluna executado!")
        return True

    def clicar_coordenadas_fixas(self, x_rel, y_rel, tipo_clique='single', pausar=1.0):
        """
        Clica em coordenadas fixas relativas à janela principal.
        Útil para elementos que não mudam de posição e onde OCR é lento ou inviável.

        Args:
            x_rel, y_rel: Coordenadas relativas à janela principal.
            tipo_clique: 'single', 'double' ou 'right'.
            pausar: Tempo de espera após o clique.

        Returns:
            True se a operação foi executada, False se a janela não estiver focada.
        """
        print(f"\n🖱️  Clicando em coordenadas fixas ({x_rel}, {y_rel}) - tipo: {tipo_clique}...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela principal selecionada.")
            return False

        x_abs, y_abs = self.captura.obter_posicao_absoluta(x_rel, y_rel)

        if tipo_clique == 'double':
            pyautogui.click(x_abs, y_abs)
            time.sleep(0.1)
            pyautogui.click(x_abs, y_abs)
        elif tipo_clique == 'left':
            pyautogui.leftClick(x_abs, y_abs)
        else:  # single
            pyautogui.click(x_abs, y_abs)

        time.sleep(pausar)
        self.limpar_cache_ocr()
        print("✓ Clique em coordenadas fixas executado!")
        return True    

    def _normalizar_valor_ocr_brasil(self, texto):
        """
        Converte textos OCR no formato BR para float.

        Exemplos:
            '400,00000'   -> 400.0
            '8.640,00000' -> 8640.0
            '200'         -> 200.0
        """

        if not texto:
            return None

        texto = str(texto).strip()
        texto = re.sub(r'[^0-9.,]', '', texto)

        if not texto:
            return None

        if ',' in texto:
            texto = texto.replace('.', '').replace(',', '.')
        else:
            partes = texto.split('.')
            if len(partes) > 1:
                texto = ''.join(partes[:-1]) + '.' + partes[-1]

        try:
            return float(texto)
        except ValueError:
            return None

    def _to_float(self, valor, default=0.0):
        """
        Converte valor (int/float/str BR) para float com segurança.
        Aceita '400,00000', '8.640,00000', '200', 200, 200.0 etc.
        """
        if valor is None:
            return float(default)

        if isinstance(valor, (int, float)):
            return float(valor)

        v = self._normalizar_valor_ocr_brasil(str(valor))
        return float(v) if v is not None else float(default)

    def _to_int_str_erp(self, valor, tolerancia=1e-6):
        """
        Converte valor (int/float/str BR) para string INTEIRA (ex.: '8640').

        Aceita:
        - '8.640,00000' -> '8640'
        - '217.0'       -> '217'
        - 217           -> '217'

        Se vier fracionado de verdade (ex.: '217,5'), retorna erro (não inventa).
        """
        q = self._to_float(valor, default=None)
        if q is None:
            raise ValueError(f"Quantidade inválida: {valor!r}")

        q_arred = round(q)

        if abs(q - q_arred) > tolerancia:
            # Inteiro-only: melhor falhar do que salvar quantidade errada
            raise ValueError(f"Quantidade não-inteira para campo inteiro: {valor!r} -> {q}")

        return str(int(q_arred))
    
    def _extrair_candidatos_ocr_da_faixa(self, regiao_faixa, confianca_minima=5, preprocessing_config=None):
        """
        Executa OCR em uma faixa única da coluna Qtde. e retorna candidatos válidos.
        """

        self.limpar_cache_ocr()

        resultado_ocr = self.processar_ocr(
            regiao=regiao_faixa,
            forcar_nova=True,
            preprocessing_config=preprocessing_config
        )

        if not resultado_ocr:
            return []

        data = resultado_ocr['data']
        candidatos = []

        # aceita:
        # 400,00000
        # 8.640,00000
        # 200
        padrao_numero = r'\d{1,3}(?:\.\d{3})*,\d+|\d+,\d+|\d+'

        for i in range(len(data['text'])):
            texto = str(data['text'][i]).strip()
            if not texto:
                continue

            try:
                conf = int(float(data['conf'][i]))
            except Exception:
                conf = 0

            if conf < confianca_minima:
                continue

            encontrados = re.findall(padrao_numero, texto)
            for trecho in encontrados:
                valor = self._normalizar_valor_ocr_brasil(trecho)
                if valor is None or valor <= 0:
                    continue

                candidatos.append({
                    'texto': trecho,
                    'valor': valor,
                    'conf': conf
                })

        return candidatos

    def _gerar_faixas_linhas_coluna(self, regiao_qtde, altura_linha=18, margem_superior=0, margem_inferior=0):
        """
        Divide a região da coluna Qtde. em várias faixas horizontais.
        Cada faixa representa uma linha da grade.
        """
        x, y, w, h = regiao_qtde

        y_inicio = y + margem_superior
        h_util = h - margem_superior - margem_inferior

        if h_util <= 0:
            return []

        faixas = []
        y_atual = y_inicio

        while y_atual < y_inicio + h_util:
            altura_real = min(altura_linha, (y_inicio + h_util) - y_atual)
            faixas.append((x, y_atual, w, altura_real))
            y_atual += altura_linha

        return faixas

    def debug_faixas_coluna_qtde(self, regiao_qtde, altura_linha=18, margem_superior=0, margem_inferior=0,
                                 nome_arquivo='debug_faixas_qtde.png'):
        """
        Gera imagem de debug com as faixas das linhas desenhadas sobre a coluna Qtde.
        """
        if not self.captura.janela_atual:
            print("❌ Nenhuma janela selecionada")
            return False

        screenshot = self.captura.capturar(forcar_nova=True)
        if not screenshot:
            print("❌ Falha ao capturar screenshot")
            return False


        draw = ImageDraw.Draw(screenshot)
        faixas = self._gerar_faixas_linhas_coluna(
            regiao_qtde=regiao_qtde,
            altura_linha=altura_linha,
            margem_superior=margem_superior,
            margem_inferior=margem_inferior
        )

        for idx, (x, y, w, h) in enumerate(faixas, start=1):
            draw.rectangle([(x, y), (x + w, y + h)], outline='red', width=2)
            draw.text((x + 2, y + 2), str(idx), fill='red')

        screenshot.save(nome_arquivo)
        print(f"✓ Debug das faixas salvo em: {nome_arquivo}")
        return True

    def ler_quantidades_grade_por_linhas(self,
                                         regiao_qtde,
                                         confianca_minima=5,
                                         preprocessing_config=None,
                                         altura_linha=18,
                                         margem_superior=0,
                                         margem_inferior=0,
                                         max_linhas_vazias_seguidas=3):
        """
        Lê a coluna Qtde. separando a região em linhas.
        Mantém o código atual intacto e cria um fluxo alternativo mais assertivo.
        """
        print("\n🔍 Lendo coluna 'Qtde.' por linhas da grade...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela selecionada")
            return []

        faixas = self._gerar_faixas_linhas_coluna(
            regiao_qtde=regiao_qtde,
            altura_linha=altura_linha,
            margem_superior=margem_superior,
            margem_inferior=margem_inferior
        )

        if not faixas:
            print("❌ Nenhuma faixa de linha foi gerada")
            return []

        quantidades = []
        vazias_seguidas = 0

        for idx, faixa in enumerate(faixas, start=1):
            print(f"\n📏 Linha {idx} | faixa={faixa}")

            candidatos = self._extrair_candidatos_ocr_da_faixa(
                regiao_faixa=faixa,
                confianca_minima=confianca_minima,
                preprocessing_config=preprocessing_config
            )

            if not candidatos:
                print("   ↳ sem candidatos válidos")
                vazias_seguidas += 1

                if vazias_seguidas >= max_linhas_vazias_seguidas:
                    print("   ↳ muitas linhas vazias seguidas, encerrando leitura")
                    break

                continue

            vazias_seguidas = 0

            melhor = sorted(
                candidatos,
                key=lambda x: (x['conf'], len(str(x['texto']))),
                reverse=True
            )[0]

            quantidades.append(melhor['valor'])
            print(
                f"   ✓ melhor candidato: texto='{melhor['texto']}' | "
                f"valor={melhor['valor']} | conf={melhor['conf']}"
            )

        print(f"\n✅ Quantidades extraídas por linha: {quantidades}")
        return quantidades

    def _ler_e_processar_quantidades_grade_por_linhas(self,
                                                      regiao_qtde,
                                                      confianca_minima=5,
                                                      preprocessing_config=None,
                                                      altura_linha=18,
                                                      margem_superior=0,
                                                      margem_inferior=0):
        """
        Helper interno para leitura da coluna Qtde. por linhas.
        """
        print("\n📊 Lendo e processando quantidades da grade por linhas...")

        quantidades_grade = self.ler_quantidades_grade_por_linhas(
            regiao_qtde=regiao_qtde,
            confianca_minima=confianca_minima,
            preprocessing_config=preprocessing_config,
            altura_linha=altura_linha,
            margem_superior=margem_superior,
            margem_inferior=margem_inferior
        )

        if not quantidades_grade:
            print("⚠️  Nenhuma quantidade lida da grade por linhas.")

        return quantidades_grade
    
    def ordenar_e_verificar_quantidade_por_linhas(self,
                                                  x_qtde_header, y_qtde_header,
                                                  quantidade_n8n,
                                                  regiao_qtde,
                                                  tolerancia=0.01,
                                                  confianca_minima_ocr=5,
                                                  max_tentativas_ordenacao=3,
                                                  preprocessing_config_qtde=None,
                                                  altura_linha=18,
                                                  margem_superior=0,
                                                  margem_inferior=0):
        """
        Ordena a coluna Qtde. e lê quantidades por linhas.
        Mantém seu comportamento atual (verifica se existe algum <= N8N),
        mas agora:
          - normaliza quantidade_n8n com _to_float (aceita vírgula)
          - retorna a última lista_grade lida mesmo quando falha
        """
        print(f"\n🔄 Iniciando ordenação e verificação por linhas para quantidade N8N: {quantidade_n8n}")

        quantidade_n8n = self._to_float(quantidade_n8n)
        quantidade_encontrada_grade = 0.0
        quantidades_grade = []  # <-- guarda última leitura

        for tentativa_ordem in range(1, max_tentativas_ordenacao + 1):
            print(f"   Tentativa de ordenação {tentativa_ordem}/{max_tentativas_ordenacao}...")

            self.clicar_coordenadas_fixas(x_qtde_header, y_qtde_header, tipo_clique='double', pausar=0.7)
            time.sleep(1)

            quantidades_grade = self._ler_e_processar_quantidades_grade_por_linhas(
                regiao_qtde=regiao_qtde,
                confianca_minima=confianca_minima_ocr,
                preprocessing_config=preprocessing_config_qtde,
                altura_linha=altura_linha,
                margem_superior=margem_superior,
                margem_inferior=margem_inferior
            )

            if not quantidades_grade:
                print("⚠️  Nenhuma quantidade lida da grade após ordenação.")
                if tentativa_ordem < max_tentativas_ordenacao:
                    print("   Tentando reordenar a coluna...")
                    continue
                else:
                    print("   Máximo de tentativas de ordenação atingido sem ler quantidades.")
                    break

            print(f"   Quantidades lidas da grade: {quantidades_grade}")

            bate = False
            diferenca = 0.0

            for qtde_lida in quantidades_grade:
                diferenca = abs(qtde_lida - quantidade_n8n)
                if qtde_lida <= quantidade_n8n + tolerancia:
                    print(f"   ✅ Remessa {qtde_lida} na grade é <= N8N {quantidade_n8n}.")
                    bate = True
                    quantidade_encontrada_grade = qtde_lida
                    break

            if bate:
                return {
                    'bate': True,
                    'quantidade_encontrada_grade': quantidade_encontrada_grade,
                    'quantidade_n8n': quantidade_n8n,
                    'diferenca': diferenca,
                    'lista_grade': quantidades_grade
                }

        return {
            'bate': False,
            'quantidade_encontrada_grade': quantidade_encontrada_grade,
            'quantidade_n8n': quantidade_n8n,
            'diferenca': abs(quantidade_encontrada_grade - quantidade_n8n) if quantidade_encontrada_grade else 0.0,
            'lista_grade': quantidades_grade  # <-- aqui era [] (perdia debug)
        }
    
    def ordenar_e_ler_quantidades_por_linhas(self,
                                            x_qtde_header, y_qtde_header,
                                            regiao_qtde,
                                            confianca_minima_ocr=5,
                                            max_tentativas_ocr=3,
                                            preprocessing_config_qtde=None,
                                            altura_linha=18,
                                            margem_superior=0,
                                            margem_inferior=0):
        """
        Só faz: ordenar coluna + ler lista de quantidades.
        Tenta novamente APENAS se o OCR vier vazio (não fica alternando ordenação por lógica de negócio).
        """
        ultima_lista = []

        for tentativa in range(1, max_tentativas_ocr + 1):
            print(f"   Ordenar+Ler Qtde (tentativa OCR {tentativa}/{max_tentativas_ocr})...")

            # Ordena (seu comportamento atual)
            self.clicar_coordenadas_fixas(x_qtde_header, y_qtde_header, tipo_clique='double', pausar=0.7)
            time.sleep(1)

            lista = self._ler_e_processar_quantidades_grade_por_linhas(
                regiao_qtde=regiao_qtde,
                confianca_minima=confianca_minima_ocr,
                preprocessing_config=preprocessing_config_qtde,
                altura_linha=altura_linha,
                margem_superior=margem_superior,
                margem_inferior=margem_inferior
            ) or []

            ultima_lista = lista

            if lista:
                return lista  # ✅ lista boa, acabou

            print("⚠️  OCR retornou lista vazia.")

        return ultima_lista

    def conferir_quantidade_menor_ou_igual_por_linhas(self,
                                                    x_qtde_header, y_qtde_header,
                                                    quantidade_n8n,
                                                    regiao_qtde,
                                                    tolerancia=0.01,
                                                    confianca_minima_ocr=5,
                                                    max_tentativas_ocr=2,
                                                    preprocessing_config_qtde=None,
                                                    altura_linha=18,
                                                    margem_superior=0,
                                                    margem_inferior=0):
        """
        ROBÔ 1: Confere se existe alguma remessa <= N8N.
        """
        q_n8n = self._to_float(quantidade_n8n)

        lista_grade = self.ordenar_e_ler_quantidades_por_linhas(
            x_qtde_header=x_qtde_header,
            y_qtde_header=y_qtde_header,
            regiao_qtde=regiao_qtde,
            confianca_minima_ocr=confianca_minima_ocr,
            max_tentativas_ocr=max_tentativas_ocr,
            preprocessing_config_qtde=preprocessing_config_qtde,
            altura_linha=altura_linha,
            margem_superior=margem_superior,
            margem_inferior=margem_inferior
        )

        if not lista_grade:
            return {
                'bate': False,
                'quantidade_encontrada_grade': 0.0,
                'quantidade_n8n': q_n8n,
                'diferenca': 0.0,
                'lista_grade': []
            }

        for q in lista_grade:
            qf = self._to_float(q)
            if qf <= q_n8n + tolerancia:
                return {
                    'bate': True,
                    'quantidade_encontrada_grade': qf,
                    'quantidade_n8n': q_n8n,
                    'diferenca': abs(qf - q_n8n),
                    'lista_grade': lista_grade
                }

        return {
            'bate': False,
            'quantidade_encontrada_grade': 0.0,
            'quantidade_n8n': q_n8n,
            'diferenca': 0.0,
            'lista_grade': lista_grade
        }
    
    # ============================================================
    # HELPERS — ROBÔ 2 (MONTAGEM): SELECIONAR LINHA COM QTDE >= N8N
    # ============================================================

    def escolher_linha_por_qtde_maior_ou_igual(self, lista_grade, quantidade_n8n, tolerancia=0.01):
        """
        Seleção:
          1) pega a primeira linha com qtde ~= N8N (dif <= tolerancia)
          2) senão, pega a linha com MENOR qtde que seja >= N8N
          3) se não existir, retorna None
        """
        q_n8n = self._to_float(quantidade_n8n)

        iguais = []
        maiores = []

        for i, q in enumerate(lista_grade):
            qf = self._to_float(q)
            if abs(qf - q_n8n) <= tolerancia:
                iguais.append((i, qf))
            elif qf > q_n8n + tolerancia:
                maiores.append((i, qf))

        if iguais:
            i, qf = iguais[0]
            return {"index": i, "qtde": qf, "tipo": "igual"}

        if maiores:
            i, qf = min(maiores, key=lambda t: t[1])  # menor acima do necessário
            return {"index": i, "qtde": qf, "tipo": "maior"}

        return None

    def clicar_linha_na_coluna(self, regiao_coluna, indice_linha, altura_linha=18,
                              offset_x=20, offset_y=0, pausar=0.2):
        """
        Clica na linha N dentro de uma região (x,y,w,h) relativa à janela.
        """
        if not self.captura.janela_atual:
            print("❌ Nenhuma janela principal selecionada.")
            return False

        x, y, w, h = regiao_coluna
        x_rel = x + min(max(offset_x, 1), w - 2)
        y_rel = y + int(indice_linha * altura_linha + (altura_linha / 2)) + offset_y

        coords = self.captura.obter_posicao_absoluta(x_rel, y_rel)
        if not coords:
            print("❌ Não foi possível obter coordenadas absolutas para clicar na linha.")
            return False

        x_abs, y_abs = coords
        pyautogui.click(x_abs, y_abs)
        time.sleep(pausar)
        self.limpar_cache_ocr()
        return True

    def selecionar_linha_com_saldo_por_qtde(self,
                                        x_qtde_header, y_qtde_header,
                                        quantidade_n8n,
                                        regiao_qtde,
                                        tolerancia=0.01,
                                        confianca_minima_ocr=5,
                                        max_tentativas_ordenacao=3,
                                        preprocessing_config_qtde=None,
                                        altura_linha=18,
                                        margem_superior=0,
                                        margem_inferior=0,
                                        offset_click_x=20,
                                        offset_click_y=0):
        """
        ROBÔ 2:
        - tenta ordenar (double) + ler + escolher linha >= N8N
        - repete a ordenação se ainda não encontrar linha válida
        - ao selecionar, clica a seta (670,430)
        """
        q_n8n = self._to_float(quantidade_n8n)
        ultima_lista = []

        for tentativa in range(1, max_tentativas_ordenacao + 1):
            print(f"\n🔃 [ROBÔ 2] Tentativa {tentativa}/{max_tentativas_ordenacao} — ordenar (double) + ler + escolher...")

            # 1) Ordena (no seu sistema TEM que ser double)
            self.clicar_coordenadas_fixas(x_qtde_header, y_qtde_header, tipo_clique='double', pausar=0.7)
            time.sleep(1)

            # 2) Lê a lista
            lista_grade = self._ler_e_processar_quantidades_grade_por_linhas(
                regiao_qtde=regiao_qtde,
                confianca_minima=confianca_minima_ocr,
                preprocessing_config=preprocessing_config_qtde,
                altura_linha=altura_linha,
                margem_superior=margem_superior,
                margem_inferior=margem_inferior
            ) or []

            ultima_lista = lista_grade
            print(f"   📋 lista_grade: {lista_grade}")

            if not lista_grade:
                print("   ⚠️ OCR vazio; tentando ordenar/ler de novo...")
                continue

            # 3) Escolhe linha >= N8N
            escolha = self.escolher_linha_por_qtde_maior_ou_igual(
                lista_grade=lista_grade,
                quantidade_n8n=q_n8n,
                tolerancia=tolerancia
            )

            if not escolha:
                print("   ⚠️ Nenhuma linha >= N8N nesta leitura; tentando reordenar...")
                continue

            # 4) Clica na linha
            clicou = self.clicar_linha_na_coluna(
                regiao_coluna=regiao_qtde,
                indice_linha=escolha["index"],
                altura_linha=altura_linha,
                offset_x=offset_click_x,
                offset_y=offset_click_y,
                pausar=0.2
            )

            if not clicou:
                print("   ⚠️ Falhou clique na linha; tentando de novo...")
                continue

            time.sleep(1)

            # 5) Clica a seta para subir PN para a grade superior
            self.clicar_coordenadas_fixas(670, 430, tipo_clique='single', pausar=0.8)

            return {
                "ok": True,
                "motivo": None,
                "quantidade_n8n": q_n8n,
                "lista_grade": lista_grade,
                "linha_index": escolha["index"],
                "qtde_lida": escolha["qtde"],
                "tipo_escolha": escolha["tipo"],
                "tentativa": tentativa
            }

        return {
            "ok": False,
            "motivo": f"Falhou após {max_tentativas_ordenacao} tentativas (ordenar/ler/selecionar)",
            "quantidade_n8n": q_n8n,
            "lista_grade": ultima_lista
        }
        
    def clicar_coordenadas_multiclick(self, x_rel, y_rel, clicks=4, intervalo=0.08, pausar=0.3):
        """
        Clica N vezes no mesmo ponto (útil para forçar foco/coluna em grids).
        """
        if not self.captura.janela_atual:
            print("❌ Nenhuma janela principal selecionada.")
            return False

        x_abs, y_abs = self.captura.obter_posicao_absoluta(x_rel, y_rel)
        pyautogui.click(x_abs, y_abs, clicks=clicks, interval=intervalo)
        time.sleep(pausar)
        self.limpar_cache_ocr()
        return True

    def _formatar_quantidade_para_erp(self, quantidade, casas_decimais=5):
        """
        Formata quantidade para colar no ERP.
        - Se vier string, preserva (ex: '8.640,00000' ou '640,00000')
        - Se vier número, formata em pt-BR (vírgula decimal).
        """
        if quantidade is None:
            return ""

        if isinstance(quantidade, str):
            return quantidade.strip()

        try:
            q = float(quantidade)
            return f"{q:.{casas_decimais}f}".replace(".", ",")
        except Exception:
            return str(quantidade).strip()

    def detectar_y_linha_destacada_por_pixels(
        self,
        regiao,  # (x, y, w, h) de uma área da grade ONDE o highlight aparece bem
        limiar_escuro=120,            # mais alto que 85 (85 é bem agressivo)
        dark_frac_min=0.55,           # % de pixels escuros para considerar “linha destacada”
        min_altura_px=8,
        salvar_debug=False,
        nome_debug="debug_destaque.png"
    ):
        """
        Detecta o Y (relativo à janela) da linha destacada olhando pixels escuros.
        Estratégia robusta: por linha, mede fração de pixels abaixo de limiar_escuro.

        Retorno:
        {ok, motivo, y_rel, segmento, score_escuro}
        """
        if not self.captura.janela_atual:
            return {"ok": False, "motivo": "Nenhuma janela selecionada", "y_rel": None, "segmento": None, "score_escuro": None}

        x, y, w, h = regiao
        img_pil = self.captura.capturar_regiao(x, y, w, h)
        if not img_pil:
            return {"ok": False, "motivo": "Falha ao capturar região", "y_rel": None, "segmento": None, "score_escuro": None}

        img = np.array(img_pil.convert("L"))  # 0=preto, 255=branco

        # Fração de pixels escuros por linha
        dark_frac = (img < limiar_escuro).mean(axis=1)  # 0..1
        mask = dark_frac >= dark_frac_min

        melhor = None  # (inicio, fim, score)
        i = 0
        while i < len(mask):
            if not mask[i]:
                i += 1
                continue
            inicio = i
            while i < len(mask) and mask[i]:
                i += 1
            fim = i - 1

            altura = fim - inicio + 1
            if altura >= min_altura_px:
                # score: quanto MAIOR dark_frac médio, mais “preto”
                score = float(dark_frac[inicio:fim+1].mean())
                if (melhor is None) or (score > melhor[2]) or (score == melhor[2] and altura > (melhor[1] - melhor[0] + 1)):
                    melhor = (inicio, fim, score)

        if salvar_debug:
            try:
                dbg = img_pil.copy().convert("RGB")
                draw = ImageDraw.Draw(dbg)
                if melhor:
                    y0, y1, _ = melhor
                    draw.rectangle([(0, y0), (w - 1, y1)], outline=(255, 0, 0), width=2)
                dbg.save(nome_debug)
            except Exception as e:
                print(f"⚠️ Falha ao salvar debug: {e}")

        if not melhor:
            info = {
                "limiar_escuro": limiar_escuro,
                "dark_frac_min": dark_frac_min,
                "dark_frac_max": float(dark_frac.max()) if len(dark_frac) else None,
                "dark_frac_med": float(np.median(dark_frac)) if len(dark_frac) else None,
            }
            return {"ok": False, "motivo": "Não detectou faixa destacada na região", "y_rel": None, "segmento": None, "score_escuro": None, "info": info}

        y0, y1, score = melhor
        y_centro_local = int((y0 + y1) / 2)
        y_rel = y + y_centro_local

        return {"ok": True, "motivo": None, "y_rel": y_rel, "segmento": (int(y0), int(y1)), "score_escuro": score}

    def editar_qtde_ultimo_item_com_end(
        self,
        quantidade_n8n,
        x_rel_foco_grade=321, y_rel_foco_grade=320,

        # Recomendo: recorte de uma coluna larga (ex.: Part Number),
        # onde o preto fica “bem sólido”. Ajuste conforme seu mapeamento.
        regiao_para_detectar_destaque=(240, 309, 600, 140),

        # Clique numa coluna “segura” (não-Qtde) na linha destacada, se precisar.
        # Se você realmente precisa clicar em Qtde, mantenha x_rel_qtde_click.
        x_rel_qtde_click=971,

        pausar_pos_end=0.3,
        pausar_entre_teclas=0.1,
        salvar_debug_detecao=False,
        tentativas_detecao=2
    ):
        if not self.captura.janela_atual:
            return {"ok": False, "motivo": "Nenhuma janela selecionada"}

        ok_foco = self.clicar_coordenadas_fixas(x_rel_foco_grade, y_rel_foco_grade, tipo_clique="single", pausar=0.15)
        if not ok_foco:
            return {"ok": False, "motivo": "Falha ao focar a grade"}

        # Evita estar preso em modo edição
        pyautogui.press("esc")
        time.sleep(0.05)

        # END + detectar (com retentativa)
        det = None
        for _ in range(tentativas_detecao):
            pyautogui.press("end")
            time.sleep(pausar_pos_end)

            det = self.detectar_y_linha_destacada_por_pixels(
                regiao=regiao_para_detectar_destaque,
                limiar_escuro=120,
                dark_frac_min=0.55,
                min_altura_px=8,
                salvar_debug=salvar_debug_detecao,
                nome_debug="debug_destaque.png"
            )
            if det["ok"]:
                break

        if not det or not det["ok"]:
            return {"ok": False, "motivo": f"Falha ao detectar linha destacada: {det.get('motivo')}", "detalhes": det}

        y_rel_click = det["y_rel"]

        # Clique na Qtde (se isso abrir edição automaticamente, ok)
        x_abs, y_abs = self.captura.obter_posicao_absoluta(x_rel_qtde_click, y_rel_click)
        pyautogui.click(x_abs, y_abs)
        time.sleep(0.10)

        pyautogui.hotkey("ctrl", "a")
        time.sleep(pausar_entre_teclas)
        pyautogui.press("delete")
        time.sleep(pausar_entre_teclas)

        try:
            quantidade_txt = self._to_int_str_erp(quantidade_n8n)
        except ValueError as e:
            return {"ok": False, "motivo": str(e)}

        pyperclip.copy(quantidade_txt)
        time.sleep(0.05)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.5)

        # ENTER salva
        #pyautogui.press("enter")
        #time.sleep(0.20)

        self.limpar_cache_ocr()
        time.sleep(0.2)
        return {"ok": True, "motivo": None, "qtde_colada": quantidade_txt, "y_rel_detectado": y_rel_click, "segmento_local": det["segmento"], "score_escuro": det["score_escuro"]}
    
    @staticmethod
    def data_iso_para_ddmmaaaa(data_iso: str) -> str:
        """
        Aceita '2026-02-27' e também '2026-02-27 00:00:00' / '2026-02-27T00:00:00'
        Retorna '27/02/2026'
        """
        s = str(data_iso).strip()
        if not s:
            raise ValueError("data_fatura vazia")

        # se vier com espaço ao invés de T, normaliza pro fromisoformat entender
        if " " in s and "T" not in s:
            s = s.replace(" ", "T", 1)

        dt = datetime.fromisoformat(s)
        return dt.strftime("%d/%m/%Y")