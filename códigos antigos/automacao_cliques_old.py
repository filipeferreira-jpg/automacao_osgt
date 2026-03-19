"""
Módulo de automação usando OCR (Tesseract)
Encontra textos na tela e clica neles
"""

import pyautogui
import pytesseract
import time
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

    def processar_ocr(self, regiao=None, forcar_nova=False):
        """
        Processa OCR na janela ou região específica

        Args:
            regiao: Tupla (x, y, largura, altura) relativa à janela
            forcar_nova: Se True, ignora cache

        Returns:
            Dicionário com dados do OCR
        """
        cache_key = str(regiao) if regiao else 'full'

        # Retorna cache se existir
        if not forcar_nova and cache_key in self.cache_ocr:
            print("📋 Usando OCR em cache")
            return self.cache_ocr[cache_key]

        print("🔍 Processando OCR...")

        # Captura screenshot
        if regiao:
            x, y, w, h = regiao
            screenshot = self.captura.capturar_regiao(x, y, w, h)
        else:
            screenshot = self.captura.capturar(forcar_nova=True)

        if not screenshot:
            return None

        # Processa OCR
        data = pytesseract.image_to_data(
            screenshot,
            lang='por',
            output_type=pytesseract.Output.DICT
        )

        # Guarda em cache
        self.cache_ocr[cache_key] = {
            'data': data,
            'regiao': regiao,
            'screenshot': screenshot
        }

        print(f"✓ OCR processado - {len(data['text'])} elementos detectados")
        return self.cache_ocr[cache_key]

    def limpar_cache_ocr(self):
        """Limpa o cache de OCR (usar após mudanças na tela)"""
        self.cache_ocr = {}
        self.captura.limpar_cache()
        print("🗑️  Cache OCR limpo")

    def encontrar_texto(self, texto_busca, confianca_minima=30, parcial=True, regiao=None):
        """
        Encontra um texto na tela usando OCR

        Args:
            texto_busca: Texto a procurar
            confianca_minima: Confiança mínima do OCR (0-100)
            parcial: Se True, aceita correspondência parcial
            regiao: Região específica para buscar

        Returns:
            Dict com 'texto', 'x_rel', 'y_rel', 'x_abs', 'y_abs', 'confianca'
            ou None se não encontrar
        """
        print(f"🔍 Procurando texto: '{texto_busca}'...")

        resultado_ocr = self.processar_ocr(regiao=regiao)
        if not resultado_ocr:
            return None

        data = resultado_ocr['data']
        regiao_offset = resultado_ocr['regiao']

        # Busca o texto
        for i in range(len(data['text'])):
            texto = data['text'][i].strip()
            conf = int(data['conf'][i])

            # Verifica correspondência
            if conf < confianca_minima:
                continue

            if parcial:
                encontrado = texto_busca.lower() in texto.lower()
            else:
                encontrado = texto_busca.lower() == texto.lower()

            if encontrado:
                # Calcula posição relativa (centro do texto)
                x_rel = data['left'][i] + data['width'][i] // 2
                y_rel = data['top'][i] + data['height'][i] // 2

                # Ajusta se for região específica
                if regiao_offset:
                    x_rel += regiao_offset[0]
                    y_rel += regiao_offset[1]

                # Calcula posição absoluta
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

    def encontrar_todos_textos(self, texto_busca, confianca_minima=30, regiao=None):
        """
        Encontra TODAS as ocorrências de um texto

        Returns:
            Lista de dicionários com informações de cada ocorrência
        """
        print(f"🔍 Procurando TODAS ocorrências de: '{texto_busca}'...")

        resultado_ocr = self.processar_ocr(regiao=regiao)
        if not resultado_ocr:
            return []

        data = resultado_ocr['data']
        regiao_offset = resultado_ocr['regiao']
        resultados = []

        for i in range(len(data['text'])):
            texto = data['text'][i].strip()
            conf = int(data['conf'][i])

            if conf < confianca_minima:
                continue

            if texto_busca.lower() in texto.lower():
                x_rel = data['left'][i] + data['width'][i] // 2
                y_rel = data['top'][i] + data['height'][i] // 2

                if regiao_offset:
                    x_rel += regiao_offset[0]
                    y_rel += regiao_offset[1]

                x_abs, y_abs = self.captura.obter_posicao_absoluta(x_rel, y_rel)

                resultados.append({
                    'texto': texto,
                    'x_rel': x_rel,
                    'y_rel': y_rel,
                    'x_abs': x_abs,
                    'y_abs': y_abs,
                    'confianca': conf
                })

        print(f"✓ Encontradas {len(resultados)} ocorrências")
        return resultados

    def clicar_em_texto(self, texto_busca, tipo_clique='single', pausar=1.0, 
                        confianca_minima=30, regiao=None, tentativas=3):
        """
        Encontra um texto e clica nele

        Args:
            texto_busca: Texto a procurar
            tipo_clique: 'single', 'double', 'right'
            pausar: Tempo de espera após clicar
            confianca_minima: Confiança mínima do OCR
            regiao: Região específica para buscar
            tentativas: Número de tentativas

        Returns:
            True se clicou, False caso contrário
        """
        for tentativa in range(1, tentativas + 1):
            if tentativa > 1:
                print(f"🔄 Tentativa {tentativa}/{tentativas}...")
                self.limpar_cache_ocr()
                time.sleep(1)

            resultado = self.encontrar_texto(
                texto_busca, 
                confianca_minima=confianca_minima,
                regiao=regiao
            )

            if resultado:
                print(f"🖱️  Clicando em '{resultado['texto']}' - tipo: {tipo_clique}")

                # Executa o clique
                if tipo_clique == 'double':
                    pyautogui.doubleClick(resultado['x_abs'], resultado['y_abs'])
                elif tipo_clique == 'right':
                    pyautogui.rightClick(resultado['x_abs'], resultado['y_abs'])
                else:
                    pyautogui.click(resultado['x_abs'], resultado['y_abs'])

                time.sleep(pausar)
                self.limpar_cache_ocr()

                print("✓ Clique executado!")
                return True

        print(f"❌ Não foi possível clicar em '{texto_busca}' após {tentativas} tentativas")
        return False

    def clicar_menu_barra(self, nome_menu, pausar=1.0):
        """
        Clica em menu da barra superior usando OCR

        Args:
            nome_menu: Nome do menu (ex: 'Processos de Importação')
        """
        print(f"\n📋 Clicando no menu: '{nome_menu}'")

        # Procura apenas na região da barra de menu (topo)
        regiao_menu = (0, 0, self.captura.janela_atual.width, 50)

        return self.clicar_em_texto(
            nome_menu,
            tipo_clique='single',
            pausar=pausar,
            regiao=regiao_menu
        )

    def clicar_botao_toolbar(self, nome_botao, pausar=1.0):
        """
        Clica em botão da toolbar usando OCR

        Args:
            nome_botao: Nome do botão (ex: 'Faturas', 'Processos')
        """
        print(f"\n🔘 Clicando no botão: '{nome_botao}'")

        # Procura na região da toolbar (segunda linha)
        regiao_toolbar = (0, 50, self.captura.janela_atual.width, 100)

        return self.clicar_em_texto(
            nome_botao,
            tipo_clique='single',
            pausar=pausar,
            regiao=regiao_toolbar,
            confianca_minima=25  # Menor confiança pois são ícones com texto pequeno
        )

    def listar_todos_textos(self, confianca_minima=30):
        """
        Lista TODOS os textos detectados na tela (útil para debug)
        """
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
                textos.append({
                    'texto': texto,
                    'confianca': conf
                })
                print(f"✓ '{texto}' (confiança: {conf}%)")

        print("="*60)
        print(f"Total: {len(textos)} textos")
        print("="*60 + "\n")

        return textos

    def criar_mapa_visual(self, nome_arquivo='mapa_ocr.png'):
        """
        Cria imagem visual com retângulos em todos os textos detectados
        """
        print("🎨 Criando mapa visual do OCR...")

        resultado_ocr = self.processar_ocr(forcar_nova=True)
        if not resultado_ocr:
            return False

        screenshot = resultado_ocr['screenshot'].copy()
        data = resultado_ocr['data']
        draw = ImageDraw.Draw(screenshot)

        # Desenha retângulo em cada texto
        for i in range(len(data['text'])):
            texto = data['text'][i].strip()
            conf = int(data['conf'][i])

            if texto and conf > 30:
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]

                # Retângulo vermelho
                draw.rectangle(
                    [(x, y), (x + w, y + h)],
                    outline='red',
                    width=2
                )

                # Texto ao lado
                try:
                    draw.text((x, y - 15), texto[:20], fill='red')
                except:
                    pass

        screenshot.save(nome_arquivo)
        print(f"✓ Mapa visual salvo: {nome_arquivo}")
        return True
    
    def aguardar_janela_interna(self, texto_titulo, timeout=10, intervalo=1):
        """
        Aguarda uma janela INTERNA (MDI) aparecer
        Detecta pelo título que aparece na barra da janela interna

        Args:
            texto_titulo: Texto do título (ex: 'Faturas de Importação')
            timeout: Tempo máximo de espera
            intervalo: Intervalo entre verificações

        Returns:
            True se janela interna apareceu, False caso contrário
        """
        print(f"⏳ Aguardando janela interna '{texto_titulo}' aparecer...")

        inicio = time.time()
        while time.time() - inicio < timeout:
            self.limpar_cache_ocr()

            # Procura o texto na região superior (onde fica o título da janela MDI)
            regiao_titulo = (200, 100, self.captura.janela_atual.width - 200, 100)

            resultado = self.encontrar_texto(
                texto_titulo,
                confianca_minima=25,
                regiao=regiao_titulo
            )

            if resultado:
                print(f"✓ Janela interna '{texto_titulo}' detectada!")
                return True

            time.sleep(intervalo)

        print(f"❌ Timeout: janela interna '{texto_titulo}' não apareceu em {timeout}s")
        return False

    def verificar_janela_interna_aberta(self, texto_titulo, confianca_minima=25):
        """
        Verifica se uma janela interna está aberta (sem aguardar)

        Args:
            texto_titulo: Texto do título da janela
            confianca_minima: Confiança mínima do OCR

        Returns:
            True se está aberta, False caso contrário
        """
        print(f"🔍 Verificando se janela interna '{texto_titulo}' está aberta...")

        # Força nova captura
        self.limpar_cache_ocr()

        # Procura na região superior
        if not self.captura.janela_atual:
            print("❌ Nenhuma janela principal selecionada")
            return False

        regiao_titulo = (200, 100, self.captura.janela_atual.width - 200, 100)

        resultado = self.encontrar_texto(
            texto_titulo,
            confianca_minima=confianca_minima,
            regiao=regiao_titulo
        )

        if resultado:
            print(f"✓ Janela interna '{texto_titulo}' está aberta")
            return True
        else:
            print(f"❌ Janela interna '{texto_titulo}' não está aberta")
            return False

    def clicar_botao_mais_janela_interna(self, pausar=1.0):
        """
        Clica no botão + (Novo) em janelas internas MDI

        O botão + geralmente fica no canto superior esquerdo da janela interna,
        aproximadamente em (258, 147) relativo à janela principal

        Args:
            pausar: Tempo de espera após clicar

        Returns:
            True se clicou, False caso contrário
        """
        print("\n➕ Clicando no botão '+' da janela interna...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela selecionada")
            return False

        # MÉTODO 1: Tentar OCR primeiro (procura o ícone + na região da toolbar da janela interna)
        print("🔍 Tentando localizar botão '+' via OCR...")
        regiao_toolbar_interna = (230, 130, 100, 50)  # Região da toolbar da janela MDI

        resultado = self.encontrar_texto(
            '+',
            confianca_minima=20,
            regiao=regiao_toolbar_interna
        )

        if resultado:
            print(f"✓ Botão '+' encontrado via OCR em ({resultado['x_abs']}, {resultado['y_abs']})")
            pyautogui.click(resultado['x_abs'], resultado['y_abs'])
            time.sleep(pausar)
            self.limpar_cache_ocr()
            return True

        # MÉTODO 2: Usar coordenadas fixas (baseado na sua imagem)
        print("⚠️  OCR não encontrou, usando coordenadas fixas...")

        # O botão + está em aproximadamente (258, 147) relativo à janela principal
        x_abs, y_abs = self.captura.obter_posicao_absoluta(263, 150)

        print(f"🖱️  Clicando em ({x_abs}, {y_abs})...")
        pyautogui.click(x_abs, y_abs)
        time.sleep(pausar)
        self.limpar_cache_ocr()

        print("✓ Clique no botão '+' executado!")
        return True
    
    def clicar_menu_composicao_janela_interna(self, pausar=1.0):
        """
        Clica no botão + (Novo) em janelas internas MDI

        O botão + geralmente fica no canto superior esquerdo da janela interna,
        aproximadamente em (258, 147) relativo à janela principal

        Args:
            pausar: Tempo de espera após clicar

        Returns:
            True se clicou, False caso contrário
        """
        print("\n➕ Clicando no menu COMPOSICAO da janela interna, aberta no + ...")

        if not self.captura.janela_atual:
            print("❌ Nenhuma janela selecionada")
            return False

        # MÉTODO 1: Tentar OCR primeiro (procura o ícone + na região da toolbar da janela interna)
        print("🔍 Tentando localizar menu COMPOSIÇÃO via OCR...")
        regiao_toolbar_interna = (230, 130, 100, 50)  # Região da toolbar da janela MDI

        resultado = self.encontrar_texto(
            'COMPOSIÇÃO',
            confianca_minima=20,
            regiao=regiao_toolbar_interna
        )

        if resultado:
            print(f"✓ Menu COMPOSIÇÃO encontrado via OCR em ({resultado['x_abs']}, {resultado['y_abs']})")
            pyautogui.click(resultado['x_abs'], resultado['y_abs'])
            time.sleep(pausar)
            self.limpar_cache_ocr()
            return True

        # MÉTODO 2: Usar coordenadas fixas (baseado na sua imagem)
        print("⚠️  OCR não encontrou, usando coordenadas fixas...")

        # O botão + está em aproximadamente (258, 147) relativo à janela principal
        x_abs, y_abs = self.captura.obter_posicao_absoluta(601, 150)

        print(f"🖱️  Clicando em ({x_abs}, {y_abs})...")
        pyautogui.click(x_abs, y_abs)
        time.sleep(pausar)
        self.limpar_cache_ocr()

        print("✓ Clique no menu COMPOSIÇÃO executado!")
        return True
