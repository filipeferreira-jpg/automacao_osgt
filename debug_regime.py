import pyautogui
from models.captura_tela import CapturaTela
from models.automacao_cliques import AutomacaoOCR
import time

# 1) Garantir que a janela "Import" está aberta e com a grade visível
auto_ocr = AutomacaoOCR('Import')  # isso já foca a janela

captura = auto_ocr.captura
time.sleep(0.5)
x, y = captura.obter_posicao_absoluta(892, 35) #COORDENADAS 1024X768
pyautogui.click(x, y)

# Use esse loop pra testar diferentes regiões até achar a perfeita
regioes_teste = [
    # x_rel, y_rel, largura, altura, nome_arquivo
    (290, 290, 415, 130, 'grid_moeda.png'),
    #(520, 160, 180, 120, 'grid_popup.png'),
    #(940, 309, 71, 85, 'grid_montagem.png'),
    
]

for x, y, w, h, nome in regioes_teste:
    print(f"\nTestando região: ({x}, {y}, {w}, {h}) -> {nome}")
    img = captura.capturar_regiao(x, y, w, h, salvar=True, nome_arquivo=nome)
    if img:
        print(f"  💾 Salvo: {nome}")
    else:
        print("  ❌ Falha ao capturar região")

print("\nAbra os arquivos qtde_teste_*.png e veja qual está centralizada na coluna 'Qtde.'")
