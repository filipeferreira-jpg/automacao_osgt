# ============================================================
# DIAGNÓSTICO DE DRAG — Testa o arraste da coluna Agrupamento
# Mostra coordenadas absolutas e testa diferentes abordagens
# ============================================================
import time
import sys
import pyautogui
import pyperclip
from models.automacao_cliques import AutomacaoOCR

auto_ocr = AutomacaoOCR('Import')

janela = auto_ocr.captura.janela_atual
if not janela:
    print("❌ Janela 'Import' não encontrada.")
    sys.exit(1)

print(f"📐 Janela: {janela.width}x{janela.height} em ({janela.left}, {janela.top})")

# Coordenadas relativas que você está usando
X_INICIO_REL = 762
Y_DRAG       = 300
X_FIM_REL    = 640

# Converte para absolutas (para ver exatamente onde o mouse vai)
x_ini_abs, y_abs   = auto_ocr.captura.obter_posicao_absoluta(X_INICIO_REL, Y_DRAG)
x_fim_abs, _       = auto_ocr.captura.obter_posicao_absoluta(X_FIM_REL, Y_DRAG)

print(f"\n📍 Ponto INÍCIO (relativo):  ({X_INICIO_REL}, {Y_DRAG})")
print(f"📍 Ponto INÍCIO (absoluto):  ({x_ini_abs}, {y_abs})")
print(f"📍 Ponto FIM    (relativo):  ({X_FIM_REL}, {Y_DRAG})")
print(f"📍 Ponto FIM    (absoluto):  ({x_fim_abs}, {y_abs})")
print(f"📍 Deslocamento em pixels:   {abs(x_fim_abs - x_ini_abs)} px para a esquerda")

print("\n" + "=" * 60)
print("TESTES DISPONÍVEIS:")
print("  [1] Mover mouse até o INÍCIO do drag (sem clicar) — para conferir visualmente")
print("  [2] Mover mouse até o FIM  do drag (sem clicar) — para conferir visualmente")
print("  [3] Testar drag LENTO (delays maiores — 0.5s entre eventos)")
print("  [4] Testar drag MUITO LENTO (delays grandes — 1.0s entre eventos)")
print("  [5] Testar drag com win32api (método alternativo)")
print("  [6] Só mover o mouse no ponto de início e AGUARDAR 5s (você clica manualmente)")
print("  [0] Sair")
print("=" * 60)

while True:
    escolha = input("\n▶ Opção: ").strip()

    if escolha == "0":
        break

    elif escolha == "1":
        print(f"\n🖱️  Movendo para INÍCIO: ({x_ini_abs}, {y_abs}) — confira se está no separador de coluna")
        pyautogui.moveTo(x_ini_abs, y_abs, duration=0.5)
        print("✅ Mouse posicionado. Verifique na tela se está no separador correto.")
        input("   (Pressione Enter para continuar...)")

    elif escolha == "2":
        print(f"\n🖱️  Movendo para FIM: ({x_fim_abs}, {y_abs})")
        pyautogui.moveTo(x_fim_abs, y_abs, duration=0.5)
        print("✅ Mouse posicionado no destino final.")
        input("   (Pressione Enter para continuar...)")

    elif escolha == "3":
        print("\n🔍 Drag LENTO (delays 0.5s entre eventos)...")
        print(f"   {x_ini_abs},{y_abs}  →  {x_fim_abs},{y_abs}")
        pyautogui.moveTo(x_ini_abs, y_abs, duration=0.3)
        time.sleep(0.5)
        pyautogui.mouseDown(button='left')
        time.sleep(0.5)
        pyautogui.moveTo(x_fim_abs, y_abs, duration=1.0)
        time.sleep(0.3)
        pyautogui.mouseUp(button='left')
        print("✅ Drag executado. A coluna se moveu?")

    elif escolha == "4":
        print("\n🔍 Drag MUITO LENTO (delays 1.0s entre eventos)...")
        print(f"   {x_ini_abs},{y_abs}  →  {x_fim_abs},{y_abs}")
        pyautogui.moveTo(x_ini_abs, y_abs, duration=0.5)
        time.sleep(1.0)
        pyautogui.mouseDown(button='left')
        time.sleep(1.0)
        pyautogui.moveTo(x_fim_abs, y_abs, duration=2.0)
        time.sleep(0.5)
        pyautogui.mouseUp(button='left')
        print("✅ Drag executado. A coluna se moveu?")

    elif escolha == "5":
        print("\n🔍 Tentando com win32api (método alternativo de baixo nível)...")
        try:
            import win32api
            import win32con

            # Move o mouse para o início
            win32api.SetCursorPos((x_ini_abs, y_abs))
            time.sleep(0.3)
            # Pressiona o botão esquerdo
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x_ini_abs, y_abs, 0, 0)
            time.sleep(0.5)
            # Arrasta passo a passo (simula movimento mais natural)
            total_steps = 20
            dx = (x_fim_abs - x_ini_abs) / total_steps
            for step in range(total_steps + 1):
                x_step = int(x_ini_abs + dx * step)
                win32api.SetCursorPos((x_step, y_abs))
                time.sleep(0.05)
            time.sleep(0.3)
            # Solta o botão
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x_fim_abs, y_abs, 0, 0)
            print("✅ Drag via win32api executado. A coluna se moveu?")
        except ImportError:
            print("❌ win32api não disponível. Instale com: pip install pywin32")
        except Exception as e:
            print(f"❌ Erro: {e}")

    elif escolha == "6":
        print(f"\n🖱️  Posicionando mouse em ({x_ini_abs}, {y_abs}) — VOCÊ clica e arrasta manualmente")
        print("   Aguardando 3 segundos antes de mover o mouse...")
        time.sleep(3)
        pyautogui.moveTo(x_ini_abs, y_abs, duration=0.5)
        print("✅ Mouse posicionado. Agora clique e arraste manualmente para confirmar se as coordenadas estão certas.")
        input("   (Pressione Enter quando terminar...)")

    else:
        print("⚠️  Opção não reconhecida.")

print("\n🏁 Diagnóstico encerrado.")
