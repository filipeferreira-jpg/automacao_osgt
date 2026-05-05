# ============================================================
# CÉLULA: CARREGAR ITENS DO N8N
# ============================================================
from models.gerenciador_itens import GerenciadorItens
import time
import pyautogui
import pyperclip
from models.captura_tela import CapturaTela
from models.automacao_cliques import AutomacaoOCR

# =========================
# CONFIG (coordenadas)
# =========================

#REGIAO_QTDE = (885, 540, 90, 150)# 1366x768
REGIAO_QTDE = (720, 515, 83, 100) # 1024x768

PREPROCESSING_QTDE = {
    'amplify_factor': 4,
    'grayscale': True,
    'contrast': 2.6,
    'threshold': 170,
    'whitelist': '0123456789,.',
    'psm': 7,
    'debug_filename_prefix': 'debug_qtde_ocr'
}


# Inicializa o gerenciador
gerenciador = GerenciadorItens(base_url='https://n8n2.titoonline.com.br')

# Carrega os itens
if not gerenciador.carregar_do_n8n(fatura_id=25):
    raise Exception("❌ Falha ao carregar itens do N8N")
# ─── LIMITADOR DE TESTE ───────────────────────────────────
gerenciador.itens = gerenciador.itens [:2]# ← Pega apenas os 5 primeiross
# CONTROLE DE ITENS
print(f"✅ {gerenciador.total_itens()} itens prontos para processar")


print("="*60)
print(f"🔄 PROCESSANDO {gerenciador.total_itens()} ITENS")
print("="*60)

auto_ocr = AutomacaoOCR('Import')
textos = auto_ocr.listar_todos_textos(confianca_minima=30)
auto_ocr.criar_mapa_visual('debug_macro-item_ocr.png')

# ─────────────────────────────────────────────────────────
# LISTAS DE CONTROLE
# ─────────────────────────────────────────────────────────
itens_nao_encontrados = []   # itens_nao_encontrados → acumula tudo que o popup "Nenhum item foi encontrado!" disparou
itens_encontrados     = []   # itens_encontrados → acumula tudo que passou sem popup
itens_divergentes_qtde = []  # itens_divergentes_qtde → acumula tudo que passou mas a quantidade não bateu (comparação entre N8N e soma da grade)

# ─────────────────────────────────────────────────────────,
#item = gerenciador.proximo_item()
#num_ordem = gerenciador.get_num_ordem(item)
# Pega o num_ordem do primeiro item SEM consumir — apenas para preencher o campo fixo
num_ordem_fatura = gerenciador.get_num_ordem(gerenciador.item_atual())

#auto_ocr.preencher_campo_por_clipboard(342,494,num_ordem,pausar=1)
#time.sleep(1)
# Preenche o campo de ordem UMA vez antes do loop
#auto_ocr.preencher_campo_por_clipboard(342, 494, num_ordem_fatura, pausar=1) #coordenadas 1366x768
auto_ocr.preencher_campo_por_clipboard(191, 494, num_ordem_fatura, pausar=1) #coordenadas 1024x768
# As coordenadas (955, 525) e (965, 525) são baseadas na tela 1366x768
print("\n Ajustando largura da coluna 'Quantidade' na grade...")
#auto_ocr.arrastar_coluna_quantidade(955, 525, 972, 525, duracao_arraste=0.3, pausar=0.5)#coordenadas 1366x768
auto_ocr.arrastar_coluna_quantidade(780, 525, 797, 525, duracao_arraste=0.3, pausar=0.5)#coordenadas 1024x768
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

    # num_ordem não preenche dentro do loop pois é fixo por fatura
    # se a fatura mudar e tiver ordens diferentes, descomentar:
    # auto_ocr.preencher_campo_por_clipboard(342, 494, num_ordem, pausar=1)
    # 2. Preenche Part Number
    #sucesso = auto_ocr.preencher_campo_por_clipboard(714,494,part_number,pausar=1) #coordenadas 1366x768
    sucesso = auto_ocr.preencher_campo_por_clipboard(543,494,part_number,pausar=1) #coordenadas 1024x768
    time.sleep(1)
    
    #sucesso = auto_ocr.preencher_campo_por_clipboard(714,494,part_number,pausar=1)
    # 3. Clica em Busca
    auto_ocr.clicar_em_texto('Busca', pausar=2, confianca_minima=25)

    # 4. Clica no botão OK (que aparece após a busca) - usando coordenadas fixas porque OCR não esta mapeado para este item
    #x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(687, 409)
    #pyautogui.click(x_abs, y_abs)
    #time.sleep(2)
    #print(" Clique executado com coordenadas fixas")
     
    # ─────────────────────────────────────
    # NOVA LÓGICA: TRATAR CASO "Nenhum item foi encontrado!"
    # ─────────────────────────────────────
    # Damos uma pequena pausa pra janela de aviso aparecer, se for o caso
    time.sleep(1)
    
    if auto_ocr.detectar_popup_nenhum_item():
        print(f"⚠️  Nenhum item encontrado para: {part_number}")
        auto_ocr.fechar_popup_nenhum_item(pausar=1.0)
        print(f"➡️  Indo para o próximo item...")
        # ── Armazena o item completo na lista de não encontrados ──
        itens_nao_encontrados.append({
            'part_number': part_number,
            'num_ordem'  : num_ordem,
            'quantity'   : quantity,
            'net_price'  : net_price,
            'total_value': total_value
        })
        #print(f"➡️  [{len(itens_nao_encontrados)} não encontrado(s) até agora]")
        continue # pula para o próximo item do loop sem executar o restante do código abaixo
    
    # ── Item encontrado na grade ──
    itens_encontrados.append({
        'part_number': part_number,
        'num_ordem'  : num_ordem,
        'quantity'   : quantity,
        'net_price'  : net_price,
        'total_value': total_value
    })
    #X_QTDE_HEADER = 948 # <--- COORDENADA X DO CABEÇALHO "Qtde." (1366x768)
    X_QTDE_HEADER = 764 # 1024x768
    Y_QTDE_HEADER = 525 # <--- COORDENADA Y DO CABEÇALHO "Qtde."
    #print(f"\n⬆️⬇️ Ordenando coluna 'Qtde.' (duplo clique)...")
    #auto_ocr.clicar_coordenadas_fixas(X_QTDE_HEADER, Y_QTDE_HEADER, tipo_clique='double', pausar=1.0)
    
    
    #print("✅ Item encontrado na grade, prosseguindo...")

    # ─────────────────────────────────────
    # LÓGICA - COMPARAR SOMA DA GRADE x QUANTIDADE N8N
    # ─────────────────────────────────────
    #print("\n📊 Comparando quantidade do N8N com soma da coluna 'Qtde.' na grade...")

    #resultado_qtde = auto_ocr.verificar_soma_quantidades_grade(
    #    quantidade_n8n=quantity,
    #    tolerancia=0.01,      # pode ajustar se quiser permitir variação maior
    #    confianca_minima=10   # mesmo valor que funcionou no teste
    #) DESATIVADO PARA TESTE DA ORDENACAO
    resultado_qtde = auto_ocr.ordenar_e_verificar_quantidade(
        x_qtde_header=X_QTDE_HEADER,
        y_qtde_header=Y_QTDE_HEADER,
        quantidade_n8n=quantity,
        regiao_qtde=REGIAO_QTDE,
        tolerancia=0.01,
        confianca_minima_ocr=10,
        max_tentativas_ordenacao=2, # Tenta ordenar uma vez (menor->maior), e se não bater, reordena (maior->menor)
        preprocessing_config_qtde=PREPROCESSING_QTDE
    )
    # -----------------------------

    #if resultado_qtde['bate']:
    #    print(f"✅ Quantidade CONFERE para {part_number}.")
        # aqui segue o fluxo normal – ex: clicar em algum botão para confirmar
    if resultado_qtde['bate'] or resultado_qtde['soma_grade'] >= quantity:
        print(f"✅ Quantidade OK para {part_number}.")

    else:
        print(f"❌ Quantidade NÃO CONFERE para {part_number}!")
        print(f"   Grade: {resultado_qtde['soma_grade']} | N8N: {resultado_qtde['quantidade_n8n']}")
        print(f"   Lista na grade: {resultado_qtde['lista_grade']}")
        # Lista de itens divergentes - quantia não bateu - status será diferente na geração da planilha no N8N
        itens_divergentes_qtde.append({
            'part_number'      : part_number,
            'num_ordem'        : num_ordem,
            'quantity'   : quantity,
            'net_price'  : net_price,
            'total_value': total_value,
            #'qtde_soma_grade'  : resultado_qtde['soma_grade'],
            'lista_qtde_grade' : resultado_qtde['lista_grade'],
            'diferenca'        : resultado_qtde['diferenca']
        })

    # ─────────────────────────────────────
    # LÓGICA - COMPARAR SOMA DA GRADE x QUANTIDADE N8N
    # ─────────────────────────────────────
    
    # Se não entrou no if acima, significa que NÃO houve popup
    # (ou o OCR não detectou). Mais tarde vamos colocar aqui a leitura
    # da quantidade na grade para comparar com o N8N.
       
    print(f"✅ Item {part_number} processado!")
    

print("\n" + "="*60)
print(f"✅ Encontrados:     {len(itens_encontrados)}")
print(f"✅ Encontrados:     {len(itens_divergentes_qtde)} com divergência de quantidade")
print(f"❌ Não encontrados: {len(itens_nao_encontrados)}")
print("="*60)

# ── Envia relatório final consolidado ao N8N ──────────────
if itens_nao_encontrados or itens_divergentes_qtde or itens_encontrados:
    gerenciador.enviar_relatorio_final(
        itens_nao_encontrados=itens_nao_encontrados,
        itens_divergentes_qtde=itens_divergentes_qtde,
        itens_encontrados=itens_encontrados
    )

print("\n✅ TODOS OS ITENS PROCESSADOS!")