# ============================================================
# CÉLULA 1: IMPORTS E CONFIGURAÇÃO
# ============================================================
from models.captura_tela import CapturaTela
from models.automacao_cliques import AutomacaoOCR
import subprocess, sys
import pyautogui
import time


print("="*60)
print("🤖 AUTOMAÇÃO ONESOURCE - PASSO A PASSO")
print("="*60)
print("\n✓ Bibliotecas carregadas")
# ============================================================
# CÉLULA 2: NAVEGAR ATÉ A TELA DE IMPORT
# ============================================================
print("\n📍 ETAPA 1: Navegando de Módulos → Import")
print("-"*60)

# 1. Encontra e foca janela Módulos
captura = CapturaTela()
if not captura.encontrar_janela('Módulos'):
    raise Exception("❌ Janela Módulos não encontrada!")

captura.focar_janela()
print("✓ Janela Módulos focada")

# 2. Clica no menu desejado via OCR
auto_ocr_modulos = AutomacaoOCR('Módulos')
auto_ocr_modulos.clicar_menu_modulos('Import') # pode ser 'Import', 'Broker' ou 'In Out'


# 3. Aguarda janela Import abrir
print("\n⏳ Aguardando janela Import...")
if not captura.aguardar_janela('Import', timeout=10):
    raise Exception("❌ Janela Import não abriu!")

captura.focar_janela()
print("✓ Janela Import aberta e focada")

print("\n" + "="*60)
print("✅ ETAPA 1 CONCLUÍDA - Estamos na tela Import")
print("="*60)
# ============================================================
# CÉLULA 3: INICIALIZAR OCR NA TELA IMPORT
# ============================================================
print("\n📍 ETAPA 2: Inicializando OCR na tela Import")
print("-"*60)

# Cria instância do OCR apontando para janela Import
auto_ocr = AutomacaoOCR('Import')

print("✓ OCR inicializado e pronto para uso")
print("\n" + "="*60)
print("✅ ETAPA 2 CONCLUÍDA")
print("="*60)
# ============================================================
# CÉLULA 4: LISTAR TODOS OS TEXTOS DETECTADOS (DEBUG)
# ============================================================
print("\n📍 ETAPA 3: Listando textos detectados pelo OCR")
print("-"*60)

# Lista todos os textos que o OCR consegue ver
textos = auto_ocr.listar_todos_textos(confianca_minima=30)

print(f"\n✓ Total de {len(textos)} textos detectados")
print("\n" + "="*60)
print("✅ ETAPA 3 CONCLUÍDA")
print("="*60)
# ============================================================
# CÉLULA 5: CRIAR MAPA VISUAL (OPCIONAL)
# ============================================================
print("\n📍 ETAPA 4: Criando mapa visual do OCR")
print("-"*60)

# Cria imagem com retângulos vermelhos em todos os textos
auto_ocr.criar_mapa_visual('debug_import_ocr.png')

print("\n✓ Arquivo 'debug_import_ocr.png' salvo")
print("💡 Abra este arquivo para ver o que o OCR detectou")
print("\n" + "="*60)
print("✅ ETAPA 4 CONCLUÍDA")
print("="*60)
# ============================================================
# CÉLULA 6: CLICAR EM BOTÃO DA TOOLBAR (EXEMPLO: FATURAS)
# ============================================================
print("\n📍 ETAPA 5: Clicando no botão 'Faturas'")
print("-"*60)

#auto_ocr.limpar_cache_ocr()
# Tenta clicar usando OCR
sucesso = auto_ocr.clicar_botao_toolbar('Faturas', pausar=2)

if sucesso:
    print("\n✓ Clique em 'Faturas' executado com sucesso!")
else:
    auto_ocr.listar_todos_textos(
    confianca_minima=10
    )
    print("\n⚠️  OCR não encontrou, tentando coordenadas fixas...")
    # Fallback: usa coordenadas fixas
    x, y = captura.obter_posicao_absoluta(262, 70) #1024x768
    #x, y = captura.obter_posicao_absoluta(400, 70) #1366x768
    pyautogui.click(x, y)
    time.sleep(2)
    print("✓ Clique executado com coordenadas fixas")

print("\n" + "="*60)
print("✅ ETAPA 5 CONCLUÍDA")
print("="*60)
# ============================================================
# CÉLULA 8: CLICAR NO BOTÃO + (NOVO)
# ============================================================
time.sleep(5)  # Pausa para garantir que a tela esteja pronta
print("\n📍 ETAPA 8: Clicando no botão '+'")
print("-"*60)

# Clica no botão + da janela interna
sucesso = auto_ocr.clicar_botao_mais_janela_interna(pausar=2)

if sucesso:
    print("\n✓ Botão '+' clicado com sucesso!")

    # Captura tela após clicar (opcional)
    #auto_ocr.captura.capturar(salvar=True, nome_arquivo='04_apos_clicar_mais.png')
else:
    print("\n❌ Falha ao clicar no botão '+'")
    x, y = captura.obter_posicao_absoluta(88, 151) # coordenadas fixas 1024x768
    pyautogui.click(x, y)
    time.sleep(2)
    print(" Clique executado com coordenadas fixas")

print("\n" + "="*60)
print("✅ ETAPA 8 CONCLUÍDA")
print("="*60)
# ============================================================
# CÉLULA 9: CLICAR NO MENU COMPOSIÇÃO PARA EDITAR OS ITENS
# # ============================================================
time.sleep(5)

print("\n📍 ETAPA 9: Clicando no menu COMPOSIÇÃO ")
print("-"*60)

# Clica no menu composição da janela interna
sucesso = auto_ocr.clicar_menu_composicao_janela_interna(pausar=2)

if sucesso:
    print("\n✓ Menu 'COMPOSIÇÃO' clicado com sucesso!")

    # Captura tela após clicar (opcional)
    #auto_ocr.captura.capturar(salvar=True, nome_arquivo='04_apos_clicar_composicao.png')
else:
    print("\n❌ Falha ao clicar no menu 'COMPOSIÇÃO'")
    x, y = captura.obter_posicao_absoluta(430, 150) # coordenadas fixas 1024x768
    pyautogui.click(x, y)
    time.sleep(2)
    print(" Clique executado com coordenadas fixas")

print("\n" + "="*60)
print("✅ ETAPA 9 CONCLUÍDA")
print("="*60)
# ============================================================
# CÉLULA 10: CLICAR NO MENU COMPOSIÇÃO PARA EDITAR OS ITENS
# # ============================================================
time.sleep(5)

print("\n📍 ETAPA 10: Clicando no botão ADIÇÃO do menu composição ")
print("-"*60)

# Clica no botão ADIÇÃO do menu composição da janela interna
sucesso = auto_ocr.clicar_mais_composicao_janela_interna(pausar=2)

if sucesso:
    print("\n✓ Botão 'ADIÇÃO' do menu 'COMPOSIÇÃO' clicado com sucesso!")

    # Captura tela após clicar (opcional)
    #auto_ocr.captura.capturar(salvar=True, nome_arquivo='04_apos_clicar_composicao.png')
else:
    print("\n❌ Falha ao clicar no botão 'ADIÇÃO' do menu 'COMPOSIÇÃO'")
    x, y = captura.obter_posicao_absoluta(926, 201) # coordenadas fixas 1024x768
    pyautogui.click(x, y)
    time.sleep(2)
    print(" Clique executado com coordenadas fixas")

print("\n" + "="*60)
print("✅ ETAPA 10 CONCLUÍDA")
print("="*60)

time.sleep(2)
##################
#Separação para chamar o script load_invoice.py para processar os itens e depois retornar o resultado para o N8N.
##################
# ============================================================
# CHAMADA DO load_invoice.py
# ============================================================
print("\n📍 CHAMANDO monta_invoice.py...")
print("-"*60)

resultado = subprocess.run(
    [sys.executable, "monta_invoice.py"],
    capture_output=False,  # False = mostra output em tempo real no terminal
    text=True
)

if resultado.returncode != 0:
    print("❌ monta_invoice.py falhou! Abortando logoff.")
    raise Exception("Falha no monta_invoice.py")

print("✅ monta_invoice.py concluído com sucesso!")
