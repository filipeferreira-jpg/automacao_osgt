# CÓDIGO INICIAL PARA TESTES USANDO 
# TESSERACT PARA AUTOMACAO DO SISTEMA
# FUNCIONANDO DO TESSERACT PARECE SER MUITO LENTO
# ALÉM DA IMPLEMENTAÇÃO EM CÓDIGO SER IMENSA
# TROQUEI POR OUTRA ABORDAGEM - PYWINAUTO - TESTES SENDO REALIZADOS
# modulos/automation_osgt.py
import pyautogui
import pytesseract
import pygetwindow as gw
import time
from PIL import Image
#import matplotlib.pyplot as plt

# Configuração do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
#print("✓ Imports carregados")
# Verifica se Tesseract está funcionando
#version = pytesseract.get_tesseract_version()
#print(f"✓ Tesseract versão: {version}")

# Busca janela ONESOURCE
janelas = gw.getWindowsWithTitle('Módulos')

if janelas:
    janela = janelas[0]
    print(f"✓ Janela encontrada: {janela.title}")
    print(f"  Posição: ({janela.left}, {janela.top})")
    print(f"  Tamanho: {janela.width}x{janela.height}")
else:
    print("❌ Janela não encontrada")
    print("Janelas abertas:")
    for j in gw.getAllTitles():
        if j.strip():
            print(f"  - {j}")

# Foca e captura
janela.activate()
time.sleep(0.5)

screenshot = pyautogui.screenshot(region=(
    janela.left,
    janela.top,
    janela.width,
    janela.height
))

print("✓ Screenshot capturado")