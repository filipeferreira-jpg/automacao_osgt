# ============================================================
# CÉLULA 11: PREENCHER NÚM. ORDEM (CAMPO DE FILTRO)
# ============================================================
time.sleep(4)

print("\n📍 ETAPA 11: Preenchendo 'Núm. Ordem' no filtro")
print("-"*60)

"""PRECISO CRIAR UM SCRIPT QUE PUXE OS DADOS DO BANCO, VIA N8N, PARA PREENCHER ESTE CAMPO AUTOMATICAMENTE. POR ENQUANTO, VOU DEIXAR FIXO PARA TESTES.
    ** Necessário elaborar uma lógica para ver como será feita essa execução automática, se o robo vai ser acionado imediatamente após o envia da fatura para o n8n, ou após uma ação do usuário.
"""
# Usa coordenadas fixas para evitar ambiguidade
sucesso = auto_ocr.preencher_campo_por_clipboard(
    342,  # x_rel
    494,  # y_rel
    5500092513,  # NUM. ORDER - DEVE VIR DINAMICO DO BANCO - por enquanto fixo para testes
    pausar=1
)

if sucesso:
    print("\n✓ Campo 'Núm. Ordem' (filtro) preenchido!")
else:
    print("\n❌ Falha ao preencher 'Núm. Ordem'")

print("\n" + "="*60)
print("✅ ETAPA 11 CONCLUÍDA")
print("="*60)


# ============================================================
# CÉLULA 11: PREENCHER PART NUMBER
# ============================================================
time.sleep(2)

print("\n📍 ETAPA 11: Preenchendo 'Part Number' no filtro")
print("-"*60)

"""PRECISO CRIAR UM SCRIPT QUE PUXE OS DADOS DO BANCO, VIA N8N, PARA PREENCHER ESTE CAMPO AUTOMATICAMENTE. POR ENQUANTO, VOU DEIXAR FIXO PARA TESTES.
    ** Necessário elaborar uma lógica para ver como será feita essa execução automática, se o robo vai ser acionado imediatamente após o envia da fatura para o n8n, ou após uma ação do usuário.
"""
var_pn = "7135-580"
# Usa coordenadas fixas para evitar ambiguidade
sucesso = auto_ocr.preencher_campo_por_clipboard(
    714,  # x_rel
    494,  # y_rel
    var_pn,  # NUM. ORDER - DEVE VIR DINAMICO DO BANCO - por enquanto fixo para testes
    pausar=1
)

if sucesso:
    print("\n✓ Campo 'Part Number'  preenchido!")
else:
    print("\n❌ Falha ao preencher 'Part Number'")

print("\n" + "="*60)
print("✅ ETAPA 11 CONCLUÍDA")
print("="*60)

# ============================================================
# CÉLULA 12: CLICAR NO BOTÃO "BUSCA" (OCR)
# ============================================================
time.sleep(2)

print("\n📍 Clicando no botão 'Busca' com OCR")
print("-"*60)

# METODO IMPLEMENTADO: clicar_em_texto - que busca o texto e clica, com opções de configuração
sucesso = auto_ocr.clicar_em_texto(
    texto_busca='Busca',
    tipo_clique='single',
    pausar=2,
    confianca_minima=25,  # Confiança baixa para aceitar variações - NOTA: deve-se ter sempre o backup para clicar via coordenadas, caso o OCR falhe
    tentativas=3
)

if sucesso:
    print("\n✓ Botão 'Busca' clicado com sucesso!")
else:
    print("\n❌ Botão 'Busca' não encontrado via OCR")
    print("💡 Tentando coordenadas fixas como fallback...")

    # Fallback: coordenadas fixas
    x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(995, 492)
    pyautogui.click(x_abs, y_abs)
    time.sleep(2)
    print("✓ Clique executado com coordenadas fixas")

print("\n" + "="*60)
print("✅ BOTAO 'BUSCA' CLICADO COM SUCESSO")
print("="*60)

# ============================================================
# CÉLULA 12: CLICAR NO BOTÃO "OK" (OCR)
# ============================================================
time.sleep(2)

print("\n📍 Clicando no botão 'OK' com OCR")
print("-"*60)

# METODO IMPLEMENTADO: clicar_em_texto - que busca o texto e clica, com opções de configuração
sucesso = auto_ocr.clicar_em_texto(
    texto_busca='OK',
    tipo_clique='single',
    pausar=2,
    confianca_minima=25,  # Confiança baixa para aceitar variações - NOTA: deve-se ter sempre o backup para clicar via coordenadas, caso o OCR falhe
    tentativas=3
)

if sucesso:
    print("\n✓ Botão 'OK' clicado com sucesso!")
else:
    print("\n❌ Botão 'OK' não encontrado via OCR")
    print("💡 Tentando coordenadas fixas comoc fallback...")

    # Fallback: coordenadas fixas
    x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(687, 409)
    pyautogui.click(x_abs, y_abs)
    time.sleep(2)
    print("✓ Clique executado com coordenadas fixas")

print("\n" + "="*60)
print("✅ BOTAO 'OK' CLICADO COM SUCESSO")
print("="*60)

# ============================================================
# CÉLULA: CARREGAR ITENS DO N8N
# ============================================================
from models.gerenciador_itens import GerenciadorItens

# Inicializa o gerenciador
gerenciador = GerenciadorItens(base_url='https://n8n2.titoonline.com.br')

# Carrega os itens
if not gerenciador.carregar_do_n8n(fatura_id=9):
    raise Exception("❌ Falha ao carregar itens do N8N")

print(f"✅ {gerenciador.total_itens()} itens prontos para processar")
# ============================================================
# CÉLULA: ITERAR ITENS
# ============================================================
import pyperclip

print("="*60)
print(f"🔄 PROCESSANDO {gerenciador.total_itens()} ITENS")
print("="*60)




while gerenciador.tem_proximo():

    # Pega o próximo item
    item = gerenciador.proximo_item()
    progresso = gerenciador.progresso()

    # Extrai campos
    part_number  = gerenciador.get_part_number(item)
    num_ordem    = gerenciador.get_num_ordem(item)
    quantity     = gerenciador.get_quantity(item)
    net_price    = gerenciador.get_net_price(item)
    total_value  = gerenciador.get_total_value(item)

    print(f"\n{'─'*60}")
    print(f"📦 [{progresso['atual']}/{progresso['total']}] {part_number}")
    print(f"   Ordem: {num_ordem} | Qtde: {quantity} | Total: {total_value}")
    print("─"*60)

    # 1. Preenche Núm. Ordem
    x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(342, 494)
    pyautogui.click(x_abs, y_abs, clicks=3)
    time.sleep(0.3)
    pyperclip.copy(num_ordem)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.5)

    # 2. Preenche Part Number
    x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(404, 494)
    pyautogui.click(x_abs, y_abs, clicks=3)
    time.sleep(0.3)
    pyperclip.copy(part_number)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.5)

    # 3. Clica em Busca
    auto_ocr.clicar_em_texto('Busca', pausar=2, confianca_minima=25)

    # ─────────────────────────────────────
    # AQUI VOCÊ ADICIONA SUA LÓGICA
    # Verificações, cliques extras, etc.
    # ─────────────────────────────────────

    print(f"✅ Item {part_number} processado!")

print("\n" + "="*60)
print("✅ TODOS OS ITENS PROCESSADOS!")
print("="*60)
