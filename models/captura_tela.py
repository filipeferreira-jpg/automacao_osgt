"""
Módulo para captura e manipulação de screenshots
Reutilizável para qualquer janela da aplicação ONESOURCE
"""

import pyautogui
import pygetwindow as gw
import time
from PIL import Image
from datetime import datetime

class CapturaTela:
    """Classe para capturar screenshots de janelas específicas"""

    def __init__(self):
        self.ultima_captura = None
        self.janela_atual = None

    def encontrar_janela(self, titulo_parcial, timeout=60):
        """
        Encontra janela pelo título (busca parcial)

        Args:
            titulo_parcial: Parte do título da janela (ex: 'Módulos', 'Import')
            timeout: Tempo máximo de espera em segundos

        Returns:
            True se encontrou, False caso contrário
        """
        print(f"🔍 Procurando janela com '{titulo_parcial}'...")

        inicio = time.time()
        while time.time() - inicio < timeout:
            janelas = gw.getWindowsWithTitle(titulo_parcial)

            if janelas:
                self.janela_atual = janelas[0]
                print(f"✓ Janela encontrada: {self.janela_atual.title}")
                print(f"  📍 Posição: ({self.janela_atual.left}, {self.janela_atual.top})")
                print(f"  📏 Tamanho: {self.janela_atual.width}x{self.janela_atual.height}")
                return True

            time.sleep(0.5)

        print(f"❌ Janela com '{titulo_parcial}' não encontrada em {timeout}s")
        self._listar_janelas()
        return False

    def _listar_janelas(self):
        """Lista todas janelas abertas (para debug)"""
        print("\n📋 Janelas abertas:")
        for janela in gw.getAllTitles():
            if janela.strip():
                print(f"  - {janela}")
        print()

    def focar_janela(self, pausar=1.0):
        """
        Foca na janela atual

        Args:
            pausar: Tempo de espera após focar

        Returns:
            True se focou, False caso contrário
        """
        if not self.janela_atual:
            print("❌ Nenhuma janela selecionada. Use encontrar_janela() primeiro.")
            return False

        try:
            # Restaura se estiver minimizada
            if self.janela_atual.isMinimized:
                self.janela_atual.restore()
                time.sleep(0.3)

            # Foca
            self.janela_atual.activate()
            time.sleep(pausar)

            print("✓ Janela focada")
            return True

        except Exception as e:
            print(f"❌ Erro ao focar janela: {e}")
            return False

    def capturar(self, salvar=False, nome_arquivo=None, forcar_nova=True):
        """
        Captura screenshot da janela atual

        Args:
            salvar: Se True, salva a imagem em arquivo
            nome_arquivo: Nome do arquivo (se None, gera automaticamente)
            forcar_nova: Se True, força nova captura (ignora cache)

        Returns:
            Objeto PIL.Image ou None
        """
        if not self.janela_atual:
            print("❌ Nenhuma janela selecionada")
            return None

        # Retorna cache se existir e não forçar nova
        if not forcar_nova and self.ultima_captura:
            print("📸 Usando screenshot em cache")
            return self.ultima_captura

        print("📸 Capturando screenshot...")

        try:
            screenshot = pyautogui.screenshot(region=(
                self.janela_atual.left,
                self.janela_atual.top,
                self.janela_atual.width,
                self.janela_atual.height
            ))

            self.ultima_captura = screenshot
            print("✓ Screenshot capturado")

            # Salva se solicitado
            if salvar:
                if not nome_arquivo:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nome_arquivo = f"screenshot_{timestamp}.png"

                screenshot.save(nome_arquivo)
                print(f"💾 Salvo: {nome_arquivo}")

            return screenshot

        except Exception as e:
            print(f"❌ Erro ao capturar: {e}")
            return None

    def capturar_regiao(self, x_rel, y_rel, largura, altura, salvar=False, nome_arquivo=None):
        """
        Captura uma região específica dentro da janela

        Args:
            x_rel, y_rel: Posição relativa à janela
            largura, altura: Dimensões da região
            salvar: Se True, salva a imagem
            nome_arquivo: Nome do arquivo

        Returns:
            Objeto PIL.Image ou None
        """
        if not self.janela_atual:
            print("❌ Nenhuma janela selecionada")
            return None

        print(f"📸 Capturando região ({x_rel}, {y_rel}, {largura}, {altura})...")

        try:
            screenshot = pyautogui.screenshot(region=(
                self.janela_atual.left + x_rel,
                self.janela_atual.top + y_rel,
                largura,
                altura
            ))

            print("✓ Região capturada")

            if salvar:
                if not nome_arquivo:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nome_arquivo = f"regiao_{timestamp}.png"

                screenshot.save(nome_arquivo)
                print(f"💾 Salvo: {nome_arquivo}")

            return screenshot

        except Exception as e:
            print(f"❌ Erro ao capturar região: {e}")
            return None

    def limpar_cache(self):
        """Limpa o cache de screenshot"""
        self.ultima_captura = None
        print("🗑️  Cache limpo")

    def obter_posicao_absoluta(self, x_rel, y_rel):
        """
        Converte posição relativa (dentro da janela) para absoluta (na tela)

        Args:
            x_rel, y_rel: Coordenadas relativas à janela

        Returns:
            Tupla (x_abs, y_abs) ou None
        """
        if not self.janela_atual:
            print("❌ Nenhuma janela selecionada")
            return None

        x_abs = self.janela_atual.left + x_rel
        y_abs = self.janela_atual.top + y_rel

        return (x_abs, y_abs)

    def aguardar_janela(self, titulo_parcial, timeout=30, intervalo=1):
        """
        Aguarda até que uma nova janela apareça
        Útil após clicar em menus que abrem novas janelas

        Args:
            titulo_parcial: Parte do título da nova janela
            timeout: Tempo máximo de espera
            intervalo: Intervalo entre verificações

        Returns:
            True se janela apareceu, False caso contrário
        """
        print(f"⏳ Aguardando janela com '{titulo_parcial}' aparecer...")

        inicio = time.time()
        while time.time() - inicio < timeout:
            if self.encontrar_janela(titulo_parcial, timeout=0.1):
                print(f"✓ Janela '{titulo_parcial}' apareceu!")
                return True

            time.sleep(intervalo)

        print(f"❌ Timeout: janela '{titulo_parcial}' não apareceu em {timeout}s")
        return False

    # Funções auxiliares para uso rápido
    def capturar_janela_rapido(titulo, salvar=False, nome_arquivo=None):
        """
        Função auxiliar: captura uma janela rapidamente

        Uso:
            screenshot = capturar_janela_rapido('Módulos', salvar=True)
        """
        captura = CapturaTela()

        if captura.encontrar_janela(titulo):
            captura.focar_janela()
            return captura.capturar(salvar=salvar, nome_arquivo=nome_arquivo)

        return None
