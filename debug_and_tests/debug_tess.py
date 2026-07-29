import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ============================================================
# teste_popup_atencao_moeda.py
# Testa detecção e fechamento do popup "Atenção! Moeda..."
# sem precisar rodar o robô completo.
#
# Como usar:
#   1. Deixe o ONESOURCE aberto na janela Import
#   2. Acione manualmente o popup (ex: clicando em Busca com
#      um item que dispara o aviso de moeda)
#   3. Execute este script — ele tentará detectar e fechar
# ============================================================
import time
import pyautogui
from models.automacao_cliques import AutomacaoOCR

# ─── CONFIG ───────────────────────────────────────────────
JANELA_ALVO = 'Import'
PAUSAR_ANTES_DE_TESTAR = 5  # segundos para você acionar o popup manualmente
# ──────────────────────────────────────────────────────────

print("=" * 60)
print("🧪 TESTE — Popup 'Atenção! Moeda...'")
print("=" * 60)

auto_ocr = AutomacaoOCR(JANELA_ALVO)

print(f"\n⏳ Aguardando {PAUSAR_ANTES_DE_TESTAR}s...")
print("   >> Acione o popup manualmente neste intervalo <<")
time.sleep(PAUSAR_ANTES_DE_TESTAR)

# ─── FASE 1: Detecção ─────────────────────────────────────
print("\n📍 FASE 1: Detectando popup...")

# Região do popup "Atenção! Moeda..." — 1024x768
# Ajuste se necessário com base no print enviado
REGIAO_POPUP_MOEDA = (290, 290, 415, 130)

auto_ocr.limpar_cache_ocr()
resultado_ocr = auto_ocr.processar_ocr(regiao=REGIAO_POPUP_MOEDA, forcar_nova=True)

textos_alvo = ['moeda', 'fatura', 'diferente', 'atenção', 'atencao', 'ordem', 'item']
textos_detectados = []

if resultado_ocr:
    data = resultado_ocr['data']
    for i in range(len(data['text'])):
        texto = data['text'][i].strip()
        if not texto:
            continue
        try:
            conf = int(data['conf'][i])
        except ValueError:
            conf = 0
        if conf < 10:
            continue
        textos_detectados.append(texto.lower())
        print(f"  📝 OCR detectou: '{texto}' (conf: {conf}%)")

texto_completo = ' '.join(textos_detectados)
popup_detectado = any(alvo in texto_completo for alvo in textos_alvo)

if popup_detectado:
    print("✅ FASE 1 OK — popup detectado na região!")
else:
    print("❌ FASE 1 FALHOU — popup não detectado")
    print("   Verifique se o popup está visível e ajuste REGIAO_POPUP_MOEDA")
    print(f"   Texto completo lido: '{texto_completo}'")

# ─── FASE 2: Fechar via OCR ───────────────────────────────
print("\n📍 FASE 2: Tentando fechar via OCR (botão OK)...")

# Região do botão OK dentro do popup
REGIAO_OK = (320, 315, 300, 110)

auto_ocr.limpar_cache_ocr()
sucesso_ocr = auto_ocr.clicar_em_texto(
    texto_busca='OK',
    tipo_clique='single',
    pausar=1.0,
    regiao=REGIAO_OK,
    confianca_minima=10,
    similaridade_minima=0.5,
    tentativas=2
)

if sucesso_ocr:
    print("✅ FASE 2 OK — OK clicado via OCR!")
else:
    # ─── FASE 3: Fallback coordenadas fixas ───────────────
    print("⚠️  FASE 2 FALHOU — tentando coordenadas fixas...")

    print("\n📍 FASE 3: Fechando via coordenadas fixas...")

    # Aguarda o usuário acionar o popup de novo se já fechou
    #print(f"⏳ Aguardando {PAUSAR_ANTES_DE_TESTAR}s para você acionar o popup novamente...")
    #time.sleep(PAUSAR_ANTES_DE_TESTAR)

    # Coordenadas relativas à janela Import — botão OK do popup Atenção
    # Ajuste x e y se o clique não bater no botão
    x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(509, 397)
    print(f"🖱️  Clicando em ({x_abs}, {y_abs})...")
    #pyautogui.click(x_abs, y_abs)
    time.sleep(1.0)
    print("✅ FASE 3 — clique em coordenadas fixas executado!")

auto_ocr.limpar_cache_ocr()

# ─── RELATÓRIO FINAL ──────────────────────────────────────
print("\n" + "=" * 60)
print("📋 RESUMO DO TESTE")
print("=" * 60)
print(f"  Popup detectado (OCR):  {'✅ SIM' if popup_detectado else '❌ NÃO'}")
print(f"  OK via OCR:             {'✅ SIM' if sucesso_ocr else '❌ NÃO — usou fallback'}")
print("=" * 60)
print("\n💡 Se as fases falharam, ajuste as variáveis:")
print("   REGIAO_POPUP_MOEDA — região de detecção do popup")
print("   REGIAO_OK          — região do botão OK")
print("   obter_posicao_absoluta(x, y) — fallback de coordenadas fixas")