import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# test_grade_ocr.py

import time
from models.automacao_cliques import AutomacaoOCR
from models.captura_tela import CapturaTela # Necessário para inicializar CapturaTela se AutomacaoOCR não o fizer diretamente com o título

# --- CONFIGURAÇÃO ---
TITULO_JANELA_ALVO = 'ONESOURCE GLOBAL TRADE - Import' # Ajuste para o título exato da sua janela
CONFIANCA_MINIMA_OCR = 10     # Confiança mínima para aceitar o texto do OCR

# Região da coluna 'Qtde.' na grade (x, y, largura, altura)
# Ajuste estas coordenadas com base na sua tela e na posição da grade.
# A imagem que você enviou sugere que a coluna Qtde. está em (890, 520, 55, 100)
REGIAO_QTDE = (890, 520, 55, 100)

# Região da coluna 'Part Number' na grade (x, y, largura, altura)
# Ajuste estas coordenadas. A imagem sugere que Part Numbers estão à esquerda de Qtde.
# Exemplo: (700, 520, 150, 100) para pegar algumas linhas de PN
REGIAO_PART_NUMBER = (700, 520, 150, 100) # Ajuste conforme a posição real na sua tela

# Configurações de pré-processamento para Quantidades
PREPROCESSING_CONFIG_QTDE = {
    'amplify_factor': 3,
    'grayscale': True,
    'contrast': 2.0,
    'threshold': 255, # Ajuste este valor (0-255) se os números não estiverem claros
    'whitelist': '0123456789,.',
    'psm': 6
}

# Configurações de pré-processamento para Part Numbers
PREPROCESSING_CONFIG_PN = {
    'amplify_factor': 3,
    'grayscale': True,
    'contrast': 2.0,
    'threshold': 150, # Ajuste este valor (0-255) se os Part Numbers não estiverem claros
    'whitelist': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-/.',
    'psm': 6
}

# --- INICIALIZAÇÃO ---
print(f"Iniciando teste de OCR para a janela: '{TITULO_JANELA_ALVO}'")
auto_ocr = AutomacaoOCR(TITULO_JANELA_ALVO)

if not auto_ocr.captura.janela_atual:
    print(f"❌ Janela '{TITULO_JANELA_ALVO}' não encontrada. Certifique-se de que está aberta e visível.")
    exit()

# --- TESTE DE LEITURA DE QUANTIDADES ---
print("\n" + "="*60)
print("INICIANDO TESTE DE LEITURA DE QUANTIDADES")
print("="*60)

# Chama o método ler_quantidades_grade com as configurações de pré-processamento
quantidades_lidas = auto_ocr.ler_quantidades_grade(
    regiao_qtde=REGIAO_QTDE,
    confianca_minima=CONFIANCA_MINIMA_OCR,
    preprocessing_config=PREPROCESSING_CONFIG_QTDE
)

print(f"\nResultados FINAIS da leitura de Quantidades: {quantidades_lidas}")
if not quantidades_lidas:
    print("⚠️ Nenhuma quantidade detectada ou todas foram descartadas com a confiança mínima.")

# --- TESTE DE LEITURA DE PART NUMBERS ---
print("\n" + "="*60)
print("INICIANDO TESTE DE LEITURA DE PART NUMBERS")
print("="*60)

# Chama o novo método ler_part_numbers_grade com as configurações de pré-processamento
part_numbers_lidos = auto_ocr.ler_part_numbers_grade(
    regiao_part_number=REGIAO_PART_NUMBER,
    confianca_minima=CONFIANCA_MINIMA_OCR,
    preprocessing_config=PREPROCESSING_CONFIG_PN
)

print(f"\nResultados FINAIS da leitura de Part Numbers: {part_numbers_lidos}")
if not part_numbers_lidos:
    print("⚠️ Nenhum Part Number detectado ou todos foram descartados com a confiança mínima.")

print("\n" + "="*60)
print("TESTE DE LEITURA DE GRADE CONCLUÍDO")
print("="*60)
print("Por favor, verifique os arquivos de debug gerados:")
print("  - 'debug_ocr_original.png' (captura original da região)")
print("  - 'debug_ocr_processada.png' (imagem após pré-processamento, crucial para ajuste)")
print("Ajuste as coordenadas REGIAO_QTDE, REGIAO_PART_NUMBER e os parâmetros 'threshold' e 'contrast'")
print("dentro de PREPROCESSING_CONFIG_QTDE/PN se os resultados não estiverem satisfatórios.")