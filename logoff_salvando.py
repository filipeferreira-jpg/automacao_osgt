from models.captura_tela import CapturaTela
from models.automacao_cliques import AutomacaoOCR
import time
import pyautogui
import pyperclip

# 1) Garantir que a janela "Import" está aberta e com a grade visível
auto_ocr = AutomacaoOCR('Import')  # isso já foca a janela

REG_INVOICE = (440, 130, 200, 180)
REGIAO_SAVE = (470, 159, 300, 220)  # (x_rel, y_rel, w, h)

PREP_SAVE = {
    "amplify_factor": 3,
    "grayscale": True,
    "contrast": 2.2,
    "threshold": 185,
    # sem whitelist (porque é texto)
    "psm": 6,       # bloco de texto
    "debug_filename_prefix": "debug_save"
}

sucesso = auto_ocr.clicar_em_texto(
    texto_busca="Invoice",             # Busca por "OK"
    tipo_clique='single',
    pausar=0.5,
    regiao=REG_INVOICE,           # Limita busca à região
    confianca_minima=10,          # Baixa confiança (OCR imperfeito)
    similaridade_minima=0.5,      # Aceita "OOK" como "OK" (65% similar)
    tentativas=2
)
time.sleep(1)
if sucesso:
    print("Menu 'Invoice' clicado via OCR!")
else:
    print("OCR falhou, usando coordenadas fixas...")
    x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(486, 148) #486, 148
    pyautogui.click(x_abs, y_abs)
    time.sleep(0.5)
    auto_ocr.limpar_cache_ocr()


# Localiza o texto 'Núm. Fatura' com OCR para depois preencher o campo  
res_fatura = auto_ocr.encontrar_texto(
    texto_busca="Núm. Fatura", # texto que queremos encontrar
    confianca_minima=10,  # baixa confiança porque é texto
    regiao=REGIAO_SAVE, # ou None pra tela inteira
    similaridade_minima=0.45,
    preprocessing_config=PREP_SAVE
)
time.sleep(1)
# Clica na posição do campo 'Núm. Fatura' e preenche usando o clipboard
if res_fatura:
    x_campo = res_fatura["x_rel"] + 170   # ajuste fino: 140~250
    y_campo = res_fatura["y_rel"]
    x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(x_campo, y_campo)
    pyautogui.click(x_abs, y_abs)
    time.sleep(0.15)
    #código para preencher o numero da fatura usando o clipboard (para evitar erros de OCR)
    #pyperclip.copy(gerenciador.numero_fatura)
    pyperclip.copy("12345")
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.15)
    
# Localiza o texto 'Data da Fatura' com OCR para depois preencher o campo
res_fatura = auto_ocr.encontrar_texto(
    texto_busca="Data", # texto que queremos encontrar
    confianca_minima=10,  # baixa confiança porque é texto
    regiao=REGIAO_SAVE, # ou None pra tela inteira
    similaridade_minima=0.45,
    preprocessing_config=PREP_SAVE
)
time.sleep(1)
# Clica na posição do campo 'Data da Fatura' e preenche usando o clipboard
if res_fatura:
    x_campo = res_fatura["x_rel"] + 170   # ajuste fino: 140~250
    y_campo = res_fatura["y_rel"]
    x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(x_campo, y_campo)
    pyautogui.click(x_abs, y_abs)
    time.sleep(0.15)
    #código para preencher a data da fatura usando o clipboard (para evitar erros de OCR)
    #pyperclip.copy(gerenciador.data_fatura)
    pyperclip.copy("01/01/2026")
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.15)

# Localiza o texto 'Local Cond. Venda' com OCR para depois preencher o campo
res_fatura = auto_ocr.encontrar_texto(
    texto_busca="Venda", # texto que queremos encontrar
    confianca_minima=10,  # baixa confiança porque é texto
    regiao=REGIAO_SAVE, # ou None pra tela inteira
    similaridade_minima=0.45,
    preprocessing_config=PREP_SAVE
)
# Clica na posição do campo 'Local Cond. Venda' e preenche usando o clipboard
#time.sleep(1)
if res_fatura:
    x_campo = res_fatura["x_rel"] + 170   # ajuste fino: 140~250
    y_campo = res_fatura["y_rel"]
    x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(x_campo, y_campo)
    pyautogui.click(x_abs, y_abs)
    time.sleep(0.15)
    #código para preencher a condição de venda
    pyautogui.press("down")       
    time.sleep(0.15)              
    pyautogui.press("enter")      
    time.sleep(0.15) 

# Clicando botão 'Grava' rascunho fatura
# OCR não pega aqui, pois é um ícone
x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(230, 245)
# botão 'Grava' da fatura
pyautogui.click(x_abs, y_abs)

# Tenta clicar usando OCR
sucesso = auto_ocr.clicar_menu_barra('Windows', pausar=2)

if sucesso:
    print("\n✓ Clique em 'Windows' executado com sucesso!")
    time.sleep(2)
else:
    print("\n⚠️  OCR não encontrou, tentando coordenadas fixas...")
    # Fallback: usa coordenadas fixas
    x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(886, 34)
    pyautogui.click(x_abs, y_abs)
    time.sleep(2)
    print("✓ Clique executado com coordenadas fixas")
    
#sucesso = auto_ocr.clicar_em_texto('Sair do Sistema', pausar=1.0)
x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(926, 298)
pyautogui.click(x_abs, y_abs)
time.sleep(2)
# COORDENADAS CONFIRMAÇÃO - REALMENTE QUER SAIR DO SISTEMA - BOTÃO SIM (641, 401)
x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(641, 401)
pyautogui.click(x_abs, y_abs)
time.sleep(2)