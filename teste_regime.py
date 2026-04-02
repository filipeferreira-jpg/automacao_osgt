import time
import pyautogui
from models.automacao_cliques import AutomacaoOCR
from models.gerenciador_itens import GerenciadorItens

auto_ocr = AutomacaoOCR("Import")
time.sleep(0.5)

# 1) Região onde está o bloco do print (AJUSTE!)
REGIAO_REGIME = (520, 160, 200, 100)  # (x_rel, y_rel, w, h)

# 2) Preprocessamento voltado pra TEXTO (não números)
PREP_REGIME = {
    "amplify_factor": 3,
    "grayscale": True,
    "contrast": 2.2,
    "threshold": 185,
    # sem whitelist (porque é texto)
    "psm": 6,  # bloco de texto
    "debug_filename_prefix": "debug_regime"
}

res_regime = auto_ocr.encontrar_texto(
    texto_busca="Regime Aduaneiro", # texto que queremos encontrar
    confianca_minima=10,  # baixa confiança porque é texto
    regiao=REGIAO_REGIME, # ou None pra tela inteira
    similaridade_minima=0.45,
    preprocessing_config=PREP_REGIME
)

if res_regime:
    x_campo = res_regime["x_rel"] + 150   # ajuste fino: 140~250
    y_campo = res_regime["y_rel"]
    x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(x_campo, y_campo)
    pyautogui.click(x_abs, y_abs)
    time.sleep(0.15)
    #teste clique home para subir até o inicio do dropdown 
    pyautogui.press("home")
    time.sleep(0.15)
    # Variação A: já abre e aceita digitação
    pyautogui.press("1")
    time.sleep(0.15)
    pyautogui.press("esc")
    time.sleep(0.15)




#print("RESULTADO:", res)