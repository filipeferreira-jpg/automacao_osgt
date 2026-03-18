import pyautogui
import pytesseract
import pygetwindow as gw
import time
from PIL import Image

# Configuração do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

print("="*60)
print("🔍 DEBUG TESSERACT")
print("="*60)

# 1. Encontra janela
print("\n📌 Procurando janela...")
janelas = gw.getWindowsWithTitle('Módulos')

if not janelas:
    print("❌ Janela não encontrada!")
    exit()

janela = janelas[0]
print(f"✓ Janela: {janela.title}")
print(f"  Posição: left={janela.left}, top={janela.top}")
print(f"  Tamanho: {janela.width}x{janela.height}")

# 2. Foca
janela.activate()
time.sleep(1)

# 3. Captura screenshot DA TELA INTEIRA (para comparar)
print("\n📸 Capturando tela inteira...")
screenshot_full = pyautogui.screenshot()
screenshot_full.save('debug_tela_inteira.png')
print("✓ Salvo: debug_tela_inteira.png")

# 4. Captura apenas a região da janela
print("\n📸 Capturando região da janela...")
screenshot_janela = pyautogui.screenshot(region=(
    janela.left,
    janela.top,
    janela.width,
    janela.height
))
screenshot_janela.save('debug_janela.png')
print("✓ Salvo: debug_janela.png")

# 5. Testa OCR na tela inteira
print("\n🔍 Testando OCR na tela inteira...")
texto_full = pytesseract.image_to_string(screenshot_full, lang='por')
print("Texto detectado (tela inteira):")
print("-" * 60)
print(texto_full)
print("-" * 60)

# 6. Testa OCR só na janela
print("\n🔍 Testando OCR na janela...")
texto_janela = pytesseract.image_to_string(screenshot_janela, lang='por')
print("Texto detectado (janela):")
print("-" * 60)
print(texto_janela)
print("-" * 60)

# 7. Testa OCR com preprocessamento (melhorar contraste)
print("\n🔍 Testando OCR com pré-processamento...")
from PIL import ImageEnhance

# Aumenta contraste
enhancer = ImageEnhance.Contrast(screenshot_janela)
img_contraste = enhancer.enhance(2.0)
img_contraste.save('debug_contraste.png')

texto_contraste = pytesseract.image_to_string(img_contraste, lang='por')
print("Texto detectado (com contraste):")
print("-" * 60)
print(texto_contraste)
print("-" * 60)

# 8. Testa com image_to_data (mais detalhado)
print("\n🔍 Testando com image_to_data...")
data = pytesseract.image_to_data(
    screenshot_janela,
    lang='por',
    output_type=pytesseract.Output.DICT
)

print(f"\nTotal de elementos detectados: {len(data['text'])}")
print("\nTextos com confiança > 30:")
for i in range(len(data['text'])):
    texto = data['text'][i].strip()
    conf = int(data['conf'][i])
    if texto and conf > 30:
        print(f"  ✓ '{texto}' (confiança: {conf}%)")

print("\n" + "="*60)
print("✓ Debug concluído!")
print("\nVerifique as imagens salvas:")
print("  - debug_tela_inteira.png")
print("  - debug_janela.png")
print("  - debug_contraste.png")
