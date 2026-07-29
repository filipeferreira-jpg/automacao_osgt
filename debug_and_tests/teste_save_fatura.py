import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
import pyautogui
import pyperclip
from models.automacao_cliques import AutomacaoOCR
from models.gerenciador_itens import GerenciadorItens

auto_ocr = AutomacaoOCR("Import")
#gerenciador = GerenciadorItens(base_url='https://n8n2.titoonline.com.br')
#sucesso = gerenciador.carregar_do_n8n(fatura_id=25)

# 1) Região onde está o bloco do print (AJUSTE!)
REGIAO_SAVE = (470, 159, 300, 220)  # (x_rel, y_rel, w, h)
OK_RASCUNHO = (950, 639, 140, 45)
REG_INVOICE = (400, 200, 400, 300)

# 2) Preprocessamento voltado pra TEXTO (não números)
PREP_SAVE = {
    "amplify_factor": 3,
    "grayscale": True,
    "contrast": 2.2,
    "threshold": 185,
    # sem whitelist (porque é texto)
    "psm": 6,  # bloco de texto
    "debug_filename_prefix": "debug_save"
}


'''
# Usando método existente da classe AutomacaoOCR
sucesso = auto_ocr.clicar_em_texto(
    texto_busca="OK",             # Busca por "OK"
    tipo_clique='single',
    pausar=0.5,
    regiao=OK_RASCUNHO,           # Limita busca à região
    confianca_minima=10,          # Baixa confiança (OCR imperfeito)
    similaridade_minima=0.5,      # Aceita "OOK" como "OK" (65% similar)
    tentativas=2
)

if sucesso:
    print("OK clicado via OCR!")
else:    
    print("OCR falhou, usando coordenadas fixas...")
    x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(1015, 656)
    pyautogui.click(x_abs, y_abs)
    time.sleep(0.5)
    auto_ocr.limpar_cache_ocr()

pyautogui.hotkey("s")  # Ctrl+S para salvar
time.sleep(0.5)
#coordenada 'SIM' do popup de confirmação de moeda da fatura
#(630, 399)



res_fatura = auto_ocr.encontrar_texto(
    texto_busca="Núm. Fatura", # texto que queremos encontrar
    confianca_minima=10,  # baixa confiança porque é texto
    regiao=REGIAO_SAVE, # ou None pra tela inteira
    similaridade_minima=0.45,
    preprocessing_config=PREP_SAVE
)

if res_fatura:
    x_campo = res_fatura["x_rel"] + 170   # ajuste fino: 140~250
    y_campo = res_fatura["y_rel"]
    x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(x_campo, y_campo)
    pyautogui.click(x_abs, y_abs)
    time.sleep(0.15)
    #código para preencher o numero da fatura usando o clipboard (para evitar erros de OCR)
    pyperclip.copy(gerenciador.numero_fatura)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.15)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.15)

res_data = auto_ocr.encontrar_texto(
    texto_busca="Data da", # texto que queremos encontrar
    confianca_minima=10,  # baixa confiança porque é texto
    regiao=REGIAO_SAVE, # ou None pra tela inteira
    similaridade_minima=0.45,
    preprocessing_config=PREP_SAVE
)

if res_data:
    x_campo = res_data["x_rel"] + 170   # ajuste fino: 140~250
    y_campo = res_data["y_rel"]
    x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(x_campo, y_campo)
    pyautogui.click(x_abs, y_abs)
    time.sleep(0.15)
    #código para preencher a data da fatura usando o clipboard (para evitar erros de OCR)
    pyperclip.copy(gerenciador.data_fatura)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.15)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.15)
'''