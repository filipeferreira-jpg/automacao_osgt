from models.captura_tela import CapturaTela
from models.automacao_cliques import AutomacaoOCR
import time

# 1) Garantir que a janela "Import" está aberta e com a grade visível
auto_ocr = AutomacaoOCR('Import')  # isso já foca a janela

captura = auto_ocr.captura

# Use esse loop pra testar diferentes regiões até achar a perfeita
regioes_teste = [
    # x_rel, y_rel, largura, altura, nome_arquivo
    #(820, 500, 140, 90, 'qtde_teste_1.png'),
    #(860, 500, 120, 90, 'qtde_teste_2.png'),
    (900, 520, 55, 100, 'qtde_teste_3.png'),
]

for x, y, w, h, nome in regioes_teste:
    print(f"\nTestando região: ({x}, {y}, {w}, {h}) -> {nome}")
    img = captura.capturar_regiao(x, y, w, h, salvar=True, nome_arquivo=nome)
    if img:
        print(f"  💾 Salvo: {nome}")
    else:
        print("  ❌ Falha ao capturar região")

print("\nAbra os arquivos qtde_teste_*.png e veja qual está centralizada na coluna 'Qtde.'")
