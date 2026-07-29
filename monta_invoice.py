# ============================================================
# ROBÔ 2 — MONTAGEM DO RASCUNHO (SEM RETORNO AO N8N)
# ============================================================
import time
import sys
import pyautogui
import pyperclip
from models.gerenciador_itens import GerenciadorItens
from models.automacao_cliques import AutomacaoOCR

# mapeamento de regições para OCR

# =========================
# CONFIG (coordenadas)
# =========================
### REGIÃO ONDE SELECIONAMOS O REGIME ADUANEIRO NO - RASCUNHO DA FATURA
#REGIAO_REGIME = (520, 160, 200, 100) #1366X768 - OK
REGIAO_REGIME = (350, 160, 200, 100) #1024x768
#### REGIÃO ONDE SE ENCONTRAM OS 3 CAMPOS QUE PRECISAMOS PREENCHER PARA SALVAR O RASCUNHO DA FATURA
#### SÃO ELES : NUMERO FATURA, DATA FATURA E LOCAL CONDIÇÃO DE VENDA
#REGIAO_SAVE = (470, 159, 300, 220) #1366X768- OK
REGIAO_SAVE = (295, 159, 300, 220) #1024x768
#### REGIÃO ONDE ESTÁ LOCALIZA A EXATAMENTE A GRADE DE QUANTIDADES,
#### JÁ APLICADA O ARRASTO DA GRADE PARA AUMENTAR A COLUNA DE QUANTIDADES
#REGIAO_QTDE = (885, 540, 90, 150) #1366X768- OK
REGIAO_QTDE = (720, 540, 80, 70) #1024x768
### REGIÃO ONDE ESTÁ LOCALIZADO BOTÃO OK NA MONTAGEM DO RASCUNHO DA FATURA
#OK_RASCUNHO = (950, 639, 140, 45) #1366X768- OK
OK_RASCUNHO = (780, 639, 120, 45) #1024x768
#REG_INVOICE = (440, 130, 200, 180) #1366X768- OK
REG_INVOICE = (280, 130, 200, 180) #1024x768
### COORDENADAS PARA CLICAR VIA COORDENADAS NO CAMPO ORDEM
#X_ORDEM = 342 #1366X768
X_ORDEM = 191 #coordenadas 1024x768- OK
Y_ORDEM = 494
### COORDENADAS PARA CLICAR VIA COORDENADAS NO CAMPO PART NUMBER
#X_PARTNUMBER = 714 #1366X768- OK
X_PARTNUMBER = 543 #1024x768
Y_PARTNUMBER = 494
### COORDENADAS PARA ARRASTAR A LINHA DA QTDE, MELHORA A VISUALIZAÇÃO PARA OCR
#X_QTDE_HEADER = 948 #1366X768- OK
Y_QTDE_HEADER = 525 #1366X768- OK
X_QTDE_HEADER = 780 #1024x768


PREP_REGIME = {
    "amplify_factor": 3,
    "grayscale": True,
    "contrast": 2.2,
    "threshold": 185,
    # sem whitelist (porque é texto)
    "psm": 6,  # bloco de texto
    "debug_filename_prefix": "debug_regime"
}

PREPROCESSING_QTDE = {
    'amplify_factor': 5,
    'grayscale': True,
    'contrast': 2.2,
    'threshold': 160,
    'whitelist': '0123456789,.',
    'psm': 7,
    'debug_filename_prefix': 'debug_qtde_ocr'
}

PREP_SAVE = {
    "amplify_factor": 3,
    "grayscale": True,
    "contrast": 2.2,
    "threshold": 185,
    # sem whitelist (porque é texto)
    "psm": 6,  # bloco de texto
    "debug_filename_prefix": "debug_save"
}

# =========================
# INIT
# =========================
gerenciador = GerenciadorItens(base_url='https://n8n2.titoonline.com.br')

if not gerenciador.carregar_do_n8n(fatura_id=126): #PARA TESTES
    raise Exception("❌ Falha ao carregar itens do N8N")

# limitador de teste
gerenciador.itens = gerenciador.itens#[:30]  # Processa apenas os primeiros 50 itens

print(f"✅ {gerenciador.total_itens()} itens prontos para montar rascunho")
print("=" * 60)
print(f"🔄 PROCESSANDO {gerenciador.total_itens()} ITENS (MONTAGEM)")
print("=" * 60)

auto_ocr = AutomacaoOCR('Import')

# =========================
# LISTAS (log interno)
# =========================
itens_nao_encontrados = []
itens_sem_saldo = []
itens_selecionados = []


# =========================
# Preenche ordem UMA vez (sem consumir item)
# =========================
num_ordem_fatura = gerenciador.get_num_ordem(gerenciador.item_atual())
auto_ocr.preencher_campo_por_clipboard(X_ORDEM, Y_ORDEM, num_ordem_fatura, pausar=1)

# --- AJUSTE DINÂMICO DE ARRASTE E CLIQUE DE ORDENAÇÃO NA TABELA INFERIOR ---
print("🔍 Detectando cabeçalho 'Qtde.' na tabela inferior...")
regiao_inferior = (200, 500, 700, 45) # Região aproximada do cabeçalho da Tabela Inferior (Y ≈ 525)
res_inf = auto_ocr.encontrar_texto("Qtde", confianca_minima=10, regiao=regiao_inferior, similaridade_minima=0.55)

if res_inf:
    x_header_inf = res_inf['x_rel']
    y_header_inf = res_inf['y_rel']
    x_divisoria_inf = x_header_inf + 40 # divisória direita
    x_destino_inf = x_divisoria_inf + 17 # alarga a coluna em 17px para a direita
    print(f"↔️ Executando arraste dinâmico inferior: de ({x_divisoria_inf}, {y_header_inf}) para ({x_destino_inf}, {y_header_inf})")
    auto_ocr.arrastar_coluna_quantidade(x_divisoria_inf, y_header_inf, x_destino_inf, y_header_inf, duracao_arraste=0.3, pausar=0.5)
    
    # Atualiza as variáveis globais para a ordenação dinâmica
    X_QTDE_HEADER = x_header_inf
    Y_QTDE_HEADER = y_header_inf
else:
    print("⚠️ Não foi possível encontrar 'Qtde.' na tabela inferior. Usando fallbacks estáticos...")
    auto_ocr.arrastar_coluna_quantidade(780, 525, 797, 525, duracao_arraste=0.3, pausar=0.5)
    X_QTDE_HEADER = 780
    Y_QTDE_HEADER = 525

# Cliques para alinhar a grade "Itens da Fatura" (7 cliques aprovados)
auto_ocr.clicar_coordenadas_multiclick(908, 392, clicks=7, intervalo=0.5, pausar=0.5) #coordenadas 1024x768

# --- AJUSTE DINÂMICO DE ARRASTE ---
print("🔍 Detectando cabeçalho 'Qtde.' para arraste dinâmico...")
regiao_cabeçalho = (200, 275, 700, 45) # Região do cabeçalho da Tabela Superior (Y ≈ 300)
res_sup = auto_ocr.encontrar_texto("Qtde", confianca_minima=10, regiao=regiao_cabeçalho, similaridade_minima=0.55)

if res_sup:
    x_divisoria = res_sup['x_rel'] - 40
    y_cabeçalho = res_sup['y_rel']
    x_destino = x_divisoria - 150 # Arraste dinâmico de 150 pixels aprovado
    print(f"↔️ Executando arraste dinâmico: de ({x_divisoria}, {y_cabeçalho}) para ({x_destino}, {y_cabeçalho})")
    auto_ocr.arrastar_coluna_quantidade(x_divisoria, y_cabeçalho, x_destino, y_cabeçalho, duracao_arraste=0.4, pausar=1.0)
else:
    print("⚠️ Não foi possível encontrar 'Qtde.' via OCR. Usando fallback estático...")
    auto_ocr.arrastar_coluna_quantidade(654, 300, 504, 300, duracao_arraste=0.4, pausar=1.0)

# --- CAPTURA DE COORDENADAS DINÂMICAS PARA EDIÇÃO ---
print("🔍 Capturando novas coordenadas de edição pós-arraste...")
auto_ocr.limpar_cache_ocr() # Limpa cache para ler o novo estado da tela

res_qtde_atual = auto_ocr.encontrar_texto("Qtde", confianca_minima=10, regiao=regiao_cabeçalho, similaridade_minima=0.55)
if res_qtde_atual:
    x_edicao_qtde = res_qtde_atual['x_rel']
    print(f"✓ Coluna 'Qtde.' detectada para clique em X = {x_edicao_qtde}")
else:
    x_edicao_qtde = 570 # Fallback seguro (660 - 90)
    print(f"⚠️ 'Qtde.' não localizada pós-arraste. Usando fallback X = {x_edicao_qtde}")
    
res_vunit_atual = auto_ocr.encontrar_texto("Valor Unitário", confianca_minima=10, regiao=regiao_cabeçalho, similaridade_minima=0.80)
if res_vunit_atual:
    x_edicao_vunit = res_vunit_atual['x_rel']
    print(f"✓ Coluna 'Valor Unitário' detectada para clique em X = {x_edicao_vunit}")
else:
    x_edicao_vunit = 742 # Fallback seguro (832 - 90)
    print(f"⚠️ 'Valor Unitário' não localizado pós-arraste. Usando fallback X = {x_edicao_vunit}")
# =========================
# LOOP ITENS
# =========================
while gerenciador.tem_proximo():
    
    item = gerenciador.proximo_item()
    progresso = gerenciador.progresso()

    part_number = gerenciador.get_part_number(item)
    quantity = gerenciador.get_quantity(item)
    net_price = gerenciador.get_net_price(item)
    total_value = gerenciador.get_total_value(item)
    num_ordem = gerenciador.get_num_ordem(item)
    item_id = gerenciador.get_id(item)

    print(f"\n{'─' * 60}")
    print(f"🧾 [{progresso['atual']}/{progresso['total']}] PN: {part_number}")
    print(f"   Ordem: {num_ordem} | Qtde N8N: {quantity} | Total: {total_value}")
    print("─" * 60)

    # Preenche PN e busca
    time.sleep(0.3)
    auto_ocr.preencher_campo_por_clipboard(X_PARTNUMBER, Y_PARTNUMBER, part_number, pausar=1)
    time.sleep(0.6)
    auto_ocr.clicar_em_texto('Busca', pausar=2, confianca_minima=25)

    # Aguarda popup (se existir)
    time.sleep(1)

    if auto_ocr.detectar_popup_nenhum_item():
        print(f"⚠️ Nenhum item encontrado para: {part_number}")
        auto_ocr.fechar_popup_nenhum_item(pausar=1.0)

        itens_nao_encontrados.append({
            'id': item_id,
            'part_number': part_number,
            'num_ordem': num_ordem,
            'quantity': quantity,
            'net_price': net_price,
            'total_value': total_value
        })
        
        continue

    # ✅ ROBÔ 2: seleciona linha com saldo suficiente (>=)
    selecao = auto_ocr.selecionar_linha_com_saldo_por_qtde(
        x_qtde_header=X_QTDE_HEADER,
        y_qtde_header=Y_QTDE_HEADER,
        quantidade_n8n=quantity,
        regiao_qtde=REGIAO_QTDE,
        tolerancia=0.01,
        confianca_minima_ocr=5,
        max_tentativas_ordenacao=2,
        preprocessing_config_qtde=PREPROCESSING_QTDE,
        altura_linha=18,
        margem_superior=0,
        margem_inferior=0,
        offset_click_x=20
    )
    
    if not selecao["ok"]:
        print(f"❌ Não foi possível selecionar linha p/ montagem do {part_number}. Motivo: {selecao['motivo']}")
        print(f"   N8N: {selecao.get('quantidade_n8n')} | Grade: {selecao.get('lista_grade')}")

        itens_sem_saldo.append({
            'id': item_id,
            'part_number': part_number,
            'num_ordem': num_ordem,
            'quantity': quantity,
            'net_price': net_price,
            'total_value': total_value,
            'motivo': selecao['motivo'],
            'lista_grade': selecao.get('lista_grade', [])
        })
        continue

    print(f"✅ Linha selecionada: idx={selecao['linha_index']} | qtde={selecao['qtde_lida']} | tipo={selecao['tipo_escolha']}")

    itens_selecionados.append({
        'id': item_id,
        'part_number': part_number,
        'num_ordem': num_ordem,
        'quantity': quantity,
        'qtde_grade': selecao['qtde_lida'],
        'linha_index': selecao['linha_index'],
        'tipo_escolha': selecao['tipo_escolha']
    })

    # --- RECALCULA COORDENADAS DINÂMICAS PARA EDIÇÃO ---
    # Limpa cache e relê os cabeçalhos para atualizar o X de Qtde e Valor Unitário.
    # Isso evita quebras caso a barra de rolagem vertical surja no meio do loop e desloque as colunas.
    auto_ocr.limpar_cache_ocr()
    res_qtde_atual = auto_ocr.encontrar_texto("Qtde", confianca_minima=10, regiao=regiao_cabeçalho, similaridade_minima=0.55)
    if res_qtde_atual:
        x_edicao_qtde = res_qtde_atual['x_rel']
        
    res_vunit_atual = auto_ocr.encontrar_texto("Valor Unitário", confianca_minima=10, regiao=regiao_cabeçalho, similaridade_minima=0.80)
    if res_vunit_atual:
        x_edicao_vunit = res_vunit_atual['x_rel']

    #print(f"✅ PN {part_number} pronto para próxima etapa da montagem.")
    time.sleep(0.8)  # dá tempo da grade superior atualizar
    res_qtde = auto_ocr.editar_qtde_ultimo_item_com_end(
        quantidade_n8n=quantity,
        x_rel_qtde_click=x_edicao_qtde,
        y_rel_foco_grade=330,  # Garante foco dentro das linhas de dados da grade superior (Y=330 em vez de Y=260)
        x_rel_foco_grade=30    # Clica na coluna seletora da extrema esquerda (evita abrir dropdowns e digitação)
    )

    # BUG #3 corrigido: verificar res_qtde["ok"] ANTES de acessar "y_rel_detectado".
    # Antes, um KeyError derrubava o loop inteiro se a detecção falhasse.
    if not res_qtde["ok"]:
        print("❌ Falha ao editar Qtde:", res_qtde["motivo"])
        continue  # pula para o próximo item sem travar o robô

    auto_ocr.editar_valor_unitario_na_linha(
        valor_unitario_n8n=net_price, 
        y_rel_click=res_qtde["y_rel_detectado"],
        x_rel_vunit_click=x_edicao_vunit
    )


print("\n" + "=" * 60)
print(f"✅ Selecionados p/ montagem: {len(itens_selecionados)}")
print(f"⚠️ Sem saldo (>=):          {len(itens_sem_saldo)}")
print(f"❌ Não encontrados:         {len(itens_nao_encontrados)}")
print("=" * 60)

# Envia relatório ao N8N antes de continuar
gerenciador.enviar_relatorio_montagem(
    itens_nao_encontrados=itens_nao_encontrados,
    itens_sem_saldo=itens_sem_saldo,
    itens_selecionados=itens_selecionados
)

print("\n✅ ROBÔ 2 - RASCUNHO DA FATURA FINALIZADO (SEM RETORNO AO N8N).")

#sys.exit(0)
# Preenchimento do campo de Regime Aduaneiro 
print("\nPreenchendo campos adicionais (Regime Aduaneiro)")
res = auto_ocr.encontrar_texto(
    texto_busca="Regime Aduaneiro", # texto que queremos encontrar
    confianca_minima=10,            # baixa confiança porque é texto
    regiao=REGIAO_REGIME,           # ou None pra tela inteira
    similaridade_minima=0.45,
    preprocessing_config=PREP_REGIME
)
print("Clicando ao lado do campo 'Regime Aduaneiro' para abrir dropdown...")
if res:
    x_campo = res["x_rel"] + 150   # ajuste fino: 140~250
    y_campo = res["y_rel"]
    x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(x_campo, y_campo)
    pyautogui.click(x_abs, y_abs)
    time.sleep(0.15)
    #teste clique home para subir até o inicio do dropdown 
    pyautogui.press("home")
    time.sleep(0.15)
    # Variação A: já abre e aceita digitação
    pyautogui.press("0") # SELECIONA DRAWBACK ISENÇÃO
    time.sleep(0.15)
    pyautogui.press("esc")
    time.sleep(0.15)



# TENTANDO CLICAR NO BOTÃO OK PARA SALVAR O RASCUNHO DOS PNS da fatura
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
    #fallback para clique fixo caso OCR falhe (com limpeza de cache para próxima tentativa)
    print("OCR falhou, usando coordenadas fixas...")
    #x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(1015, 656) # fallback 1366x768
    x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(847, 656) # fallback 1024x768
    pyautogui.click(x_abs, y_abs)
    time.sleep(0.5)
    auto_ocr.limpar_cache_ocr()
# Agora sim, salva o rascunho
# Tecla 'S' no popup que se abre para salvar o rascunho
time.sleep(1.5)
pyautogui.hotkey("s")
time.sleep(0.8)
#pyautogui.hotkey("s")
#time.sleep(2)
time.sleep(1.5)  # aguarda o popup aparecer, se for o caso
auto_ocr.fechar_popup_atencao_moeda(pausar=2.0)
# ETAPA PARA PREENCHIMENTO DE CAMPOS ADICIONAIS - NUMERO FATURA E DATA FATURA
# Localiza o texto 'Invoice' para garantir que estamos na região certa antes de preencher os campos

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
    pyperclip.copy(gerenciador.numero_fatura)
    #pyperclip.copy("12345")
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
    data_formatada = auto_ocr.data_iso_para_ddmmaaaa(gerenciador.data_fatura)
    pyperclip.copy(data_formatada) #01/01/2026
    time.sleep(0.05)
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
    
time.sleep(1)
# Clicando botão 'Grava' rascunho fatura
# OCR não pega aqui, pois é um ícone
x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(230, 245) # botão grava, janela salva rascunho - 1366x768
x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(59, 245) # botão grava, janela salva rascunho - 1366x768
# botão 'Grava' da fatura
pyautogui.click(x_abs, y_abs)
# Tenta clicar usando OCR
time.sleep(3)
#sys.exit(0)
sucesso = auto_ocr.clicar_menu_barra('Windows', pausar=2)

sys.exit(0)
if sucesso:
    print("\n✓ Clique em 'Windows' executado com sucesso!")
    time.sleep(2)
else:
    print("\n⚠️  OCR não encontrou, tentando coordenadas fixas...")
    # Fallback: usa coordenadas fixas
    x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(886, 34) # fallback 1024x768 
    #x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(886, 34) # fallback 1024x768
    pyautogui.click(x_abs, y_abs)
    time.sleep(2)
    print("✓ Clique executado com coordenadas fixas")
    
#sucesso = auto_ocr.clicar_em_texto('Sair do Sistema', pausar=1.0)
print("\n✓ Clicando botão 'Sair do Sistema'com coordenadas fixas") 
#x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(926, 298) # 1366x768
x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(756, 298) # 1024x768
pyautogui.click(x_abs, y_abs)
time.sleep(2)
# COORDENADAS CONFIRMAÇÃO - REALMENTE QUER SAIR DO SISTEMA - BOTÃO SIM (641, 401)
print("\n✓ Clicando botão 'Sim'com coordenadas fixas")
#x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(641, 401) # 1366x768
x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(465, 401) # 1024x768
pyautogui.click(x_abs, y_abs)
time.sleep(2)