from models.captura_tela import CapturaTela
from models.automacao_cliques import AutomacaoOCR
import time

auto_ocr = AutomacaoOCR('Import')
#textos = auto_ocr.listar_todos_textos(confianca_minima=15)
#auto_ocr.criar_mapa_visual('debug_macro-item_ocr.png')


if auto_ocr.detectar_popup_nenhum_item():
    print("POPUP não detectado")
    auto_ocr.fechar_popup_nenhum_item(pausar=1.0)
else:
    print("POPUP não detectado")