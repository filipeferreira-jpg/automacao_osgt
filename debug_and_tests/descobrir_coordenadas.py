import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.automacao_cliques import AutomacaoOCR
import pyautogui
import time

print("="*60)
print("🎯 DESCOBRIR COORDENADAS DO BOTÃO '+'")
print("="*60)

# Certifica que está na janela Import
auto = AutomacaoOCR('Import')

if not auto.captura.janela_atual:
    print("❌ Janela Import não encontrada")
    exit()

print("\n✓ Janela Import encontrada")
print(f"  Posição: ({auto.captura.janela_atual.left}, {auto.captura.janela_atual.top})")
print(f"  Tamanho: {auto.captura.janela_atual.width}x{auto.captura.janela_atual.height}")

print("\n" + "="*60)
print("📍 INSTRUÇÕES:")
print("="*60)
print("1. Certifique-se que a janela 'Faturas de Importação' está aberta")
print("2. Posicione o mouse SOBRE o botão '+' (circulado em vermelho)")
print("3. Aguarde 5 segundos")
print("\nIniciando contagem...\n")

for i in range(5, 0, -1):
    print(f"⏱️  {i}...")
    time.sleep(1)

# Captura posição do mouse
x_abs, y_abs = pyautogui.position()

# Calcula posição relativa
x_rel = x_abs - auto.captura.janela_atual.left
y_rel = y_abs - auto.captura.janela_atual.top

print("\n" + "="*60)
print("📊 RESULTADO:")
print("="*60)
print(f"📍 Posição ABSOLUTA (tela): ({x_abs}, {y_abs})")
print(f"📍 Posição RELATIVA (janela Import): ({x_rel}, {y_rel})")
print("\n✅ Atualize no código:")
print(f"   x, y = auto.captura.obter_posicao_absoluta({x_rel}, {y_rel})")
print("="*60)

# Testa o clique
print("\n🖱️  Quer testar o clique? (s/n)")
resposta = input().lower()

if resposta == 's':
    print("\nClicando em 3 segundos...")
    time.sleep(3)
    pyautogui.click(x_abs, y_abs)
    print("✓ Clique executado!")
