from models.captura_tela import CapturaTela
import pyautogui
import time

print("="*60)
print("🤖 AUTOMAÇÃO ONESOURCE - MÓDULOS → IMPORT")
print("="*60)

# Cria instância da classe
captura = CapturaTela()

# 1. Encontra e captura a tela de Módulos
print("\n📍 PASSO 1: Capturando tela de Módulos...")
if not captura.encontrar_janela('Módulos'):
    print("❌ Falha: janela Módulos não encontrada")
    exit()

captura.focar_janela()
captura.capturar(salvar=True, nome_arquivo='01_tela_modulos.png')

# 2. Clica no menu Import (double click)
print("\n📍 PASSO 2: Clicando no menu Import...")
x, y = captura.obter_posicao_absoluta(106, 305)  # Coordenadas do Import
print(f"🖱️  Posição do clique: ({x}, {y})")
print("Clicando em 3 segundos...")
time.sleep(3)

pyautogui.doubleClick(x, y)
print("✓ Double click executado!")

# 3. Aguarda e captura a tela de Import
print("\n📍 PASSO 3: Aguardando tela de Import abrir...")
if captura.aguardar_janela('Import', timeout=10):
    captura.focar_janela()
    captura.capturar(salvar=True, nome_arquivo='02_tela_import.png')
    print("✓ Tela de Import capturada!")
else:
    print("❌ Timeout: tela de Import não abriu")

print("\n" + "="*60)
print("✓ Processo concluído!")
print("="*60)
