# ============================================================
# CÉLULA: CARREGAR ITENS DO N8N
# ============================================================
from models.gerenciador_itens import GerenciadorItens
import time
import pyautogui
import pyperclip
from models.captura_tela import CapturaTela
from models.automacao_cliques import AutomacaoOCR

# Inicializa o gerenciador
gerenciador = GerenciadorItens(base_url='https://n8n2.titoonline.com.br')

# Carrega os itens
if not gerenciador.carregar_do_n8n(fatura_id=21):
    raise Exception("❌ Falha ao carregar itens do N8N")
# ─── LIMITADOR DE TESTE ───────────────────────────────────
gerenciador.itens = gerenciador.itens  [:5]# ← Pega apenas os 5 primeiross
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
item = gerenciador.proximo_item()
num_ordem    = gerenciador.get_num_ordem(item)

sucesso = auto_ocr.preencher_campo_por_clipboard(
342,  # x_rel
494,  # y_rel
num_ordem,  # NUM. ORDER - DEVE VIR DINAMICO DO BANCO - por enquanto fixo para testes
pausar=1
)
time.sleep(1)
sucesso = auto_ocr.preencher_campo_por_clipboard(
342,  # x_rel
494,  # y_rel
num_ordem,  # NUM. ORDER - DEVE VIR DINAMICO DO BANCO - por enquanto fixo para testes
pausar=1
)

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
    # Usa coordenadas fixas para evitar ambiguidade
    #sucesso = auto_ocr.preencher_campo_clipboard(
    #342,  # x_rel
    #494,  # y_rel
    #num_ordem,  # NUM. ORDER - DEVE VIR DINAMICO DO BANCO - por enquanto fixo para testes
    #pausar=1
    #)
    # 2. Preenche Part Number
    sucesso = auto_ocr.preencher_campo_por_clipboard(
    714,  # x_rel
    494,  # y_rel
    part_number,  # PART NUMBER - DEVE VIR DINAMICO DO BANCO - por enquanto fixo para testes
    pausar=1
    )
    # 
    time.sleep(1)
    
    sucesso = auto_ocr.preencher_campo_por_clipboard(
    714,  # x_rel
    494,  # y_rel
    part_number,  # PART NUMBER - DEVE VIR DINAMICO DO BANCO - por enquanto fixo para testes
    pausar=1
    )
    # 3. Clica em Busca
    auto_ocr.clicar_em_texto('Busca', pausar=2, confianca_minima=25)

    # 4. Clica no botão OK (que aparece após a busca) - usando coordenadas fixas porque OCR não esta mapeado para este item
    #x_abs, y_abs = auto_ocr.captura.obter_posicao_absoluta(687, 409)
    #pyautogui.click(x_abs, y_abs)
    #time.sleep(2)
    #print("✓ Clique executado com coordenadas fixas")
     
    # ─────────────────────────────────────
    # LÓGICA: OCR DETECTA PN PESQUISADO NA GRADE
    #    possível lógica: se o OCR detectar part number na grade, vamos clicar
    # ─────────────────────────────────────     
     
     
     
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
        continue
    
    # ── Item encontrado na grade ──
    itens_encontrados.append({
        'part_number': part_number,
        'num_ordem'  : num_ordem,
        'quantity'   : quantity,
        'net_price'  : net_price,
        'total_value': total_value
    })

    
    print("✅ Item encontrado na grade, prosseguindo...")

    # ─────────────────────────────────────
    # LÓGICA - COMPARAR SOMA DA GRADE x QUANTIDADE N8N
    # ─────────────────────────────────────
    print("\n📊 Comparando quantidade do N8N com soma da coluna 'Qtde.' na grade...")

    resultado_qtde = auto_ocr.verificar_soma_quantidades_grade(
        
        quantidade_n8n=quantity,
        tolerancia=0.01,      # pode ajustar se quiser permitir variação maior
        confianca_minima=10   # mesmo valor que funcionou no teste
    )

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
            'qtde_soma_grade'  : resultado_qtde['soma_grade'],
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


print("\n✅ TODOS OS ITENS PROCESSADOS!")