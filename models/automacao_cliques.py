"""
Módulo de automação usando OCR (Tesseract)
Encontra textos na tela e clica neles
"""
import win32com.client
import pyautogui
import pytesseract
import time
import pyperclip
from difflib import SequenceMatcher
from PIL import Image, ImageDraw
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

    def processar_ocr(self, regiao=None, forcar_nova=False):
        """Processa OCR na janela ou região específica"""
        cache_key = str(regiao) if regiao else 'full'

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

        data = pytesseract.image_to_data(
            screenshot,
            lang='por',
            output_type=pytesseract.Output.DICT
        )

        self.cache_ocr[cache_key] = {
            'data': data,
            'regiao': regiao,
            'screenshot': screenshot
        }

        print(f"✓ OCR processado - {len(data['text'])} elementos detectados")
        return self.cache_ocr[cache_key]

    def limpar_cache_ocr(self):
        """Limpa o cache de OCR"""
        self.cache_ocr = {}
        self.captura.limpar_cache()
        print("🗑️  Cache OCR limpo")
    """ HELPER ANTIGO PARA ENCONTRAR TEXTO, PRECISEI MODIFICAR PARA PASSAR A similaridade_minima COMO PARÂMETRO, ENTÃO DEIXEI ESSE MÉTODO ANTIGO COMENTADO PARA NÃO PERDER O CÓDIGO
    def encontrar_texto(self, texto_busca, confianca_minima=30, parcial=True, regiao=None):
        Encontra um texto na tela usando OCR
        print(f"🔍 Procurando texto: '{texto_busca}'...")

        resultado_ocr = self.processar_ocr(regiao=regiao)
        if not resultado_ocr:
            return None

        data = resultado_ocr['data']
        regiao_offset = resultado_ocr['regiao']

        for i in range(len(data['text'])):
            texto = data['text'][i].strip()
            conf = int(data['conf'][i])

            if conf < confianca_minima:
                continue

            if parcial:
                encontrado = texto_busca.lower() in texto.lower()
            else:
                encontrado = texto_busca.lower() == texto.lower()

            if encontrado:
                x_rel = data['left'][i] + data['width'][i] // 2
                y_rel = data['top'][i] + data['height'][i] // 2

                if regiao_offset:
                    x_rel += regiao_offset[0]
                    y_rel += regiao_offset[1]

                x_abs, y_abs = self.captura.obter_posicao_absoluta(x_rel, y_rel)

                resultado = {
                    'texto': texto,
                    'x_rel': x_rel,
                    'y_rel': y_rel,
                    'x_abs': x_abs,
                    'y_abs': y_abs,
                    'confianca': conf,
                    'largura': data['width'][i],
                    'altura': data['height'][i]
                }

                print(f"✓ Encontrado: '{texto}' (confiança: {conf}%)")
                print(f"  Posição relativa: ({x_rel}, {y_rel})")
                print(f"  Posição absoluta: ({x_abs}, {y_abs})")

                return resultado

        print(f"❌ Texto '{texto_busca}' não encontrado")
        return None
    """
    
    def encontrar_texto(self, texto_busca, confianca_minima=30, regiao=None, similaridade_minima=0.75):
        """Encontra texto na tela usando OCR com tolerância a erros de leitura"""

        resultado_ocr = self.processar_ocr(regiao=regiao)
        if not resultado_ocr:
            return None

        data = resultado_ocr['data']
        regiao_offset = resultado_ocr.get('regiao_offset')  # ou como está no teu código
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

                    # ✅ coordenadas reais — igual ao teu código original
                    x_rel = data['left'][i] + data['width'][i] // 2
                    y_rel = data['top'][i]  + data['height'][i] // 2

                    if regiao:
                        x_rel += regiao[0]
                        y_rel += regiao[1]

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
                        'x_abs'       : x_abs,  # ✅ valor real
                        'y_abs'       : y_abs,  # ✅ valor real
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
            'COMPOSIÇÃO',
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

    """
    
    NOVAS CLASSES DE CLIQUES ESPECÍFICOS PARA ELEMENTOS DA JANELA DE FATURA (APÓS CLICAR NO BOTÃO +):
    """
    
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
        regiao_ok = (530, 300, 280, 130)

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

    #classe para ver as quantidades com confiança muito baixa
    def ler_quantidades_grade_qualidade_baixa(self, confianca_minima=10):
        """
        Lê todas as quantidades (coluna Qtde.) da grade e retorna lista de floats.
        """

        print("\n🔍 Lendo coluna 'Qtde.' da grade de resultados...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela selecionada")
            return []

        # USE OS VALORES QUE VOCÊ MAPEOU E SÓ AUMENTE A ALTURA UM POUCO
        x_rel, y_rel, largura, altura = 900, 520, 55, 100   # ajuste aqui se necessário

        self.limpar_cache_ocr()
        screenshot = self.captura.capturar_regiao(
            x_rel, y_rel, largura, altura,
            salvar=True,
            nome_arquivo='debug_qtde_grade.png'
        )

        if not screenshot:
            print("❌ Falha ao capturar região da coluna Qtde.")
            return []

        print(f"💾 Debug salvo: 'debug_qtde_grade.png' | região: ({x_rel}, {y_rel}, {largura}, {altura})")

        # Ampliar imagem para melhorar OCR
        from PIL import Image
        img_ampliada = screenshot.resize(
            (screenshot.width * 3, screenshot.height * 3),
            Image.LANCZOS
        )
        img_ampliada.save('debug_qtde_ampliada.png')
        print("💾 Debug ampliado salvo: 'debug_qtde_ampliada.png'")

        config_tesseract = '--psm 6 -c tessedit_char_whitelist=0123456789,.'

        data = pytesseract.image_to_data(
            img_ampliada,
            lang='por',
            config=config_tesseract,
            output_type=pytesseract.Output.DICT
        )

        quantidades = []

        print("\n📜 OCR bruto na coluna Qtde.:")
        for i in range(len(data['text'])):
            texto = data['text'][i].strip()
            if not texto:
                continue

            try:
                conf = int(data['conf'][i])
            except ValueError:
                conf = 0

            print(f"  Texto='{texto}' | conf={conf}%")

            if conf < confianca_minima:
                print(f"    ↳ descartado (conf {conf}% < mínimo {confianca_minima}%)")
                continue

            normalizado = texto.replace(' ', '').replace(',', '.')
            try:
                valor = float(normalizado)
                # evita zeros de linhas vazias
                if valor == 0.0:
                    continue
                quantidades.append(valor)
                print(f"    ✓ Quantidade aceita: {valor}")
            except ValueError:
                print("    ↳ não é número, ignorado")
                continue

        print(f"\n📋 Quantidades extraídas: {quantidades}")
        return quantidades

    
    # FUNÇÃO PRINCIPAL PARA LER AS QUANTIDADES DA GRADE COM CONFIANÇA NORMAL (15% ou mais)
    def ler_quantidades_grade(self, confianca_minima=20):
        """
        Lê todas as quantidades (coluna Qtde.) da grade 'Itens da Ordem de Importação'
        e retorna uma lista de floats.

        ATENÇÃO: esta função assume que a grade já está com os resultados na tela.
        """

        print("\n🔍 Lendo coluna 'Qtde.' da grade de resultados...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela selecionada")
            return []

        # Região aproximada da coluna 'Qtde.' na grade, baseada no print:
        # A grade começa logo abaixo do filtro; coluna Qtde. está mais à direita.
        # Ajuste fino se necessário.
        #
        # x_rel, y_rel, largura, altura
        regiao_qtde = (900, 520, 55, 100)  # região para pegar só a coluna Qtde.

        # Força nova captura só dessa região
        self.limpar_cache_ocr()
        screenshot = self.captura.capturar_regiao(
            regiao_qtde[0],
            regiao_qtde[1],
            regiao_qtde[2],
            regiao_qtde[3],
            salvar=True,
            nome_arquivo='debug_qtde_grade.png'  # debug visual
        )

        if not screenshot:
            print("❌ Falha ao capturar região da coluna Qtde.")
            return []

        print("💾 Screenshot da coluna Qtde. salvo em 'debug_qtde_grade.png'")

        data = pytesseract.image_to_data(
            screenshot,
            lang='por',  # se estiver em inglês, pode trocar pra 'eng'
            output_type=pytesseract.Output.DICT
        )

        quantidades = []

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

            # Normaliza número com vírgula ou ponto
            normalizado = texto.replace('.', '').replace(',', '.')
            # exemplos:
            #  "2,00000" -> "200000" (se tiver ponto de milhar) – por isso primeiro remove ponto
            #  depois vírgula em decimal: "2,00000" -> "200000" -> isso é ruim; vamos ser menos agressivo:
            # Vamos usar uma regra mais simples: trocar só vírgula por ponto e deixar pontos.

            normalizado = texto.replace(',', '.')

            try:
                valor = float(normalizado)
                quantidades.append(valor)
                print(f"  ✓ Quantidade detectada: '{texto}' -> {valor} (conf: {conf}%)")
            except ValueError:
                # Não é número, ignora
                continue

        print(f"📋 Quantidades extraídas da grade: {quantidades}")
        return quantidades

    
    def verificar_soma_quantidades_grade(self, quantidade_n8n, tolerancia=0.01, confianca_minima=10):
        """
        Usa ler_quantidades_grade_qualidade_baixa para somar as quantidades
        da coluna Qtde. e comparar com o valor vindo do N8N.

        Args:
            quantidade_n8n: valor esperado (do N8N)
            tolerancia: diferença absoluta máxima aceitável
            confianca_minima: passado pra função de leitura, se você quiser usar

        Returns:
            dict:
            {
                'bate': True/False,
                'soma_grade': float,
                'quantidade_n8n': float,
                'diferenca': float,
                'lista_grade': [floats...]
            }
        """
        print("\n📊 Verificando soma de quantidades na grade...")

        quantidade_n8n = float(quantidade_n8n)

        # se sua função nova aceitar parâmetro de confiança, passe aqui; se não, chame direto
        quantidades_grade = self.ler_quantidades_grade_qualidade_baixa(
            confianca_minima=confianca_minima
        )

        if not quantidades_grade:
            print("⚠️  Nenhuma quantidade lida da grade.")
            return {
                'bate': False,
                'soma_grade': 0.0,
                'quantidade_n8n': quantidade_n8n,
                'diferenca': quantidade_n8n,
                'lista_grade': []
            }

        soma_grade = sum(quantidades_grade)
        diferenca = abs(soma_grade - quantidade_n8n)
        bate = diferenca <= tolerancia

        print(f"   Quantidades na grade: {quantidades_grade}")
        print(f"   Soma grade: {soma_grade}")
        print(f"   N8N:       {quantidade_n8n}")
        print(f"   Diferença: {diferenca}")

        if bate:
            print("✅ SOMA BATE com o valor do N8N.")
        else:
            print("❌ SOMA NÃO BATE com o valor do N8N.")

        return {
            'bate': bate,
            'soma_grade': soma_grade,
            'quantidade_n8n': quantidade_n8n,
            'diferenca': diferenca,
            'lista_grade': quantidades_grade
        }

    def ocr_grade_itens_ordem(self,
                              x_rel, y_rel,
                              largura, altura,
                              confianca_minima=10,
                              salvar_debug=True,
                              nome_debug='debug_grade_itens_ordem.png'):
        """
        Faz OCR da grade 'Itens da Ordem de Importação' (região destacada na imagem)
        e lista todos os textos detectados nela, com posição.

        Use primeiro só para debug / calibração de coordenadas.
        Depois podemos especializar para ler colunas específicas (Qtde, Valor, etc.).
        """
        print("\n🔍 Lendo grade 'Itens da Ordem de Importação'...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela selecionada")
            return []

        # Captura a região da grade e processa OCR
        self.limpar_cache_ocr() # Limpa o cache para garantir nova captura
        resultado_ocr = self.processar_ocr(
            regiao=(x_rel, y_rel, largura, altura),
            forcar_nova=True # Força nova captura para a região
        )

        if not resultado_ocr:
            print("❌ Falha ao processar OCR da região da grade.")
            return []

        # Salva o screenshot da região para debug
        if salvar_debug and resultado_ocr['screenshot']:
            resultado_ocr['screenshot'].save(nome_debug)
            print(f"💾 Debug da região da grade salvo: '{nome_debug}'")

        data = resultado_ocr['data']
        resultados = []

        print("\n📜 Textos detectados na grade:")
        for i in range(len(data['text'])):
            texto = data['text'][i].strip()
            conf  = int(data['conf'][i])

            if not texto:
                continue

            if conf < confianca_minima:
                # print(f"  Texto='{texto}' (conf={conf}%) - descartado por baixa confiança")
                continue

            # Coordenadas relativas à janela (somando o offset da região)
            # data['left'] e data['top'] já são relativos à screenshot da região
            # então precisamos somar o x_rel e y_rel da região para ter as coordenadas relativas à janela principal
            x_rel_texto = x_rel + data['left'][i] + data['width'][i] // 2
            y_rel_texto = y_rel + data['top'][i]  + data['height'][i] // 2

            resultados.append({
                'texto': texto,
                'conf' : conf,
                'x_rel': x_rel_texto,
                'y_rel': y_rel_texto,
                'largura': data['width'][i],
                'altura' : data['height'][i],
            })

            print(f"  ✓ '{texto}' (conf={conf}%) "
                  f"em ({x_rel_texto}, {y_rel_texto})")

        if not resultados:
            print("⚠️ Nenhum texto com confiança mínima encontrado na grade.")

        return resultados
    
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