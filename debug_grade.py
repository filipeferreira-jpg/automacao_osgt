# debug_grade_monta_invoice.py
# Foca a janela Import, captura a região da grade e roda OCR
# Sem N8N, sem loop, sem preenchimento — só mapeamento.

from models.captura_tela import CapturaTela
from models.automacao_cliques import AutomacaoOCR
from PIL import ImageDraw
import time

# ─────────────────────────────────────────────────────────
# 1. FOCA A JANELA
# ─────────────────────────────────────────────────────────
print("="*60)
print("🔍 DEBUG PARA DETECÇÃO DE GRADE ")
print("="*60)

auto_ocr = AutomacaoOCR('ONESOURCE GLOBAL TRADE - Import')  # ajuste o título se necessário

if not auto_ocr.captura.janela_atual:
    raise SystemExit(" Janela 'ONESOURCE GLOBAL TRADE - Import' não encontrada. Abra a janela e tente novamente.")

print(f"✅ Janela focada: {auto_ocr.captura.janela_atual.title}")
print(f"   Tamanho: {auto_ocr.captura.janela_atual.width}x{auto_ocr.captura.janela_atual.height}")

# ─────────────────────────────────────────────────────────
# 2. COORDENADAS DA GRADE (mapeadas por você)OK(440, 400, 120, 150) / Janela Informação(150, 320, 700, 210)
# ─────────────────────────────────────────────────────────
X_GRADE     = 550
Y_GRADE     = 290
LARGURA     = 260
ALTURA      = 130
#(530,300,280,130) - teste região OK

#(315, 315, 120, 150) - teste região OK
# ─────────────────────────────────────────────────────────
# 3. CAPTURA O PNG DA GRADE (sem OCR)
# ─────────────────────────────────────────────────────────
print(f"\n Capturando região da grade ({X_GRADE}, {Y_GRADE}, {LARGURA}, {ALTURA})...")

img = auto_ocr.captura.capturar_regiao(
    X_GRADE, Y_GRADE, LARGURA, ALTURA,
    salvar=True,
    nome_arquivo='debug_grade_raw.png'
)

if not img:
    raise SystemExit(" Falha ao capturar região da grade.")

print("💾 Salvo: debug_grade_raw.png")

# ─────────────────────────────────────────────────────────
# 4. OCR NA GRADE
# ─────────────────────────────────────────────────────────
print("\n Rodando OCR na grade...")

resultado = auto_ocr.processar_ocr(
    regiao=(X_GRADE, Y_GRADE, LARGURA, ALTURA),
    forcar_nova=True
)

if not resultado:
    raise SystemExit(" Falha no OCR.")

data = resultado['data']

# ─────────────────────────────────────────────────────────
# 5. LISTA TEXTOS COM POSIÇÃO
# ─────────────────────────────────────────────────────────
print("\n Textos detectados na grade:")
print(f"{'Texto':<30} {'X':>6} {'Y':>6} {'Conf':>6}")
print("-" * 55)

for i in range(len(data['text'])):
    texto = data['text'][i].strip()
    try:
        conf = int(data['conf'][i])
    except ValueError:
        conf = 0

    if not texto or conf < 10:
        continue

    x = data['left'][i]
    y = data['top'][i]

    print(f"{texto:<30} {x:>6} {y:>6} {conf:>5}%")

# ─────────────────────────────────────────────────────────
# 6. MAPA VISUAL COM RETÂNGULOS
# ─────────────────────────────────────────────────────────
print("\n Gerando mapa visual...")

img_debug = resultado['screenshot'].copy()
draw      = ImageDraw.Draw(img_debug)

for i in range(len(data['text'])):
    texto = data['text'][i].strip()
    try:
        conf = int(data['conf'][i])
    except ValueError:
        conf = 0

    if not texto or conf < 10:
        continue

    x = data['left'][i]
    y = data['top'][i]
    w = data['width'][i]
    h = data['height'][i]

    draw.rectangle([(x, y), (x+w, y+h)], outline='red', width=2)
    draw.text((x, y - 12), f"{texto} ({conf}%)", fill='red')

img_debug.save('debug_grade.png')
print(" Salvo: debug_grade.png")

print("\n" + "="*60)
print(" DEBUG CONCLUÍDO")
print("   Abra os arquivos abaixo para calibrar coordenadas:")
print("   → debug_grade_raw.png        (recorte puro da grade)")
print("   → debug_grade_mapa_visual.png (grade com OCR marcado)")
print("="*60)