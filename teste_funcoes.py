# ============================================================
# TESTE DE FUNÇÕES — automacao_cliques.py
# Executa cada função individualmente para validar comportamento
# SEM carregar itens do N8N
# ============================================================
import time
import sys
import pyautogui
import pyperclip
from models.automacao_cliques import AutomacaoOCR

# =========================
# CONFIG (coordenadas 1024x768)
# =========================
REGIAO_REGIME    = (350, 160, 200, 100)
REGIAO_SAVE      = (295, 159, 300, 220)
REGIAO_QTDE      = (720, 540, 80, 70)
OK_RASCUNHO      = (780, 639, 120, 45)
REG_INVOICE      = (280, 130, 200, 180)
X_ORDEM          = 191
Y_ORDEM          = 494
X_PARTNUMBER     = 543
Y_PARTNUMBER     = 494
X_QTDE_HEADER    = 780
Y_QTDE_HEADER    = 525

PREP_REGIME = {
    "amplify_factor": 3,
    "grayscale": True,
    "contrast": 2.2,
    "threshold": 185,
    "psm": 6,
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
    "psm": 6,
    "debug_filename_prefix": "debug_save"
}

# =========================
# INIT — conecta na janela Import
# =========================
print("=" * 60)
print("🔧 TESTE DE FUNÇÕES — AutomacaoOCR")
print("=" * 60)

auto_ocr = AutomacaoOCR('Import')

# ── Exibe resolução detectada da janela ──────────────────────
janela = auto_ocr.captura.janela_atual
if janela:
    print(f"\n📐 Janela detectada: '{janela.title}'")
    print(f"   Resolução: {janela.width}x{janela.height}")
    print(f"   Posição:   ({janela.left}, {janela.top})")
else:
    print("❌ Janela 'Import' não encontrada. Abra o sistema e tente novamente.")
    sys.exit(1)

# =========================
# MENU DE TESTES
# =========================
TESTES = {
    "1":  "Ajuste de tela: arrastar coluna Qtde. (grade inferior)",
    "2":  "Ajuste de tela: multiclick para alinhar grade",
    "3":  "Ajuste de tela: arrastar coluna Agrupamento",
    "4":  "Ajuste de tela: executar TODOS os 3 ajustes (como monta_invoice faz)",
    "5":  "Preencher campo Ordem (campo de filtro)",
    "6":  "Preencher campo Part Number (campo de filtro)",
    "7":  "Clicar no botão 'Busca'",
    "8":  "Detectar popup 'Nenhum item encontrado'",
    "9":  "Fechar popup 'Nenhum item encontrado'",
    "10": "Selecionar linha com saldo na grade inferior (lê OCR Qtde)",
    "11": "Clicar seta para subir item (coordenada 670, 430)",
    "12": "Editar Qtde do último item na grade superior",
    "13": "Detectar linha destacada por pixels (debug visual)",
    "14": "Editar Valor Unitário na linha detectada",
    "15": "Listar todos os textos OCR na tela inteira",
    "16": "Listar textos OCR na região REGIAO_QTDE",
    "0":  "Sair",
}

def exibir_menu():
    print("\n" + "=" * 60)
    print("🧪 SELECIONE O TESTE:")
    print("=" * 60)
    for k, v in TESTES.items():
        print(f"  [{k:>2}] {v}")
    print("=" * 60)

# =========================
# LOOP DE TESTES
# =========================
while True:
    exibir_menu()
    escolha = input("▶ Opção: ").strip()

    if escolha == "0":
        print("👋 Encerrando testes.")
        break

    print(f"\n{'─' * 60}")
    print(f"▶ Executando: {TESTES.get(escolha, '???')}")
    print(f"{'─' * 60}")
    time.sleep(0.5)  # pequena pausa para o usuário tirar o mouse do caminho

    # ── TESTE 1: arrastar coluna Qtde ────────────────────────
    if escolha == "1":
        print("🔍 Arrastando separador da coluna Qtde. (grade inferior)...")
        print("   De: (780, 525)  →  Para: (797, 525)")
        auto_ocr.arrastar_coluna_quantidade(780, 525, 797, 525, duracao_arraste=0.3, pausar=0.5)
        print("✅ Concluído. Verifique se a coluna Qtde. ficou mais larga.")

    # ── TESTE 2: multiclick para alinhar grade ───────────────
    elif escolha == "2":
        print("🔍 Dando 4 cliques na coordenada (908, 392) para alinhar a grade...")
        auto_ocr.clicar_coordenadas_multiclick(908, 392, clicks=4, intervalo=0.5, pausar=0.5)
        print("✅ Concluído. Verifique se a grade está visível e alinhada.")

    # ── TESTE 3: arrastar coluna Agrupamento ─────────────────
    elif escolha == "3":
        print("🔍 Arrastando coluna Agrupamento para a esquerda...")
        print("   De: (762, 300)  →  Para: (620, 300)")
        #auto_ocr.arrastar_coluna_quantidade(762, 300, 620, 300, duracao_arraste=0.3, pausar=0.5)
        # coordenadas testes
        auto_ocr.arrastar_coluna_quantidade(656, 300, 542, 300, duracao_arraste=0.3, pausar=0.5) 

        print("✅ Concluído. Verifique se as colunas Qtde. e Valor Unitário estão visíveis.")

    # ── TESTE 4: todos os ajustes de tela ────────────────────
    elif escolha == "4":
        print("🔍 Executando TODOS os ajustes de tela (exatamente como monta_invoice faz)...")
        print("\n[1/3] Arrastando coluna Qtde. (grade inferior)...")
        auto_ocr.arrastar_coluna_quantidade(780, 525, 797, 525, duracao_arraste=0.3, pausar=0.5)
        print("[2/3] Multiclick na grade para alinhar...")
        auto_ocr.clicar_coordenadas_multiclick(908, 392, clicks=4, intervalo=0.5, pausar=0.5)
        print("[3/3] Arrastando coluna Agrupamento para esquerda...")
        auto_ocr.arrastar_coluna_quantidade(762, 300, 620, 300, duracao_arraste=0.3, pausar=0.5)
        print("✅ Todos os ajustes concluídos.")

    # ── TESTE 5: preencher campo Ordem ───────────────────────
    elif escolha == "5":
        valor = input("   Digite o número de Ordem para testar: ").strip()
        if valor:
            auto_ocr.preencher_campo_por_clipboard(X_ORDEM, Y_ORDEM, valor, pausar=1)
            print(f"✅ Campo Ordem preenchido com '{valor}'.")
        else:
            print("⚠️ Nenhum valor digitado, pulando.")

    # ── TESTE 6: preencher campo Part Number ─────────────────
    elif escolha == "6":
        valor = input("   Digite o Part Number para testar: ").strip()
        if valor:
            auto_ocr.preencher_campo_por_clipboard(X_PARTNUMBER, Y_PARTNUMBER, valor, pausar=1)
            print(f"✅ Campo Part Number preenchido com '{valor}'.")
        else:
            print("⚠️ Nenhum valor digitado, pulando.")

    # ── TESTE 7: clicar no botão Busca ───────────────────────
    elif escolha == "7":
        print("🔍 Procurando e clicando no botão 'Busca'...")
        ok = auto_ocr.clicar_em_texto('Busca', pausar=2, confianca_minima=25)
        if ok:
            print("✅ Botão 'Busca' clicado com sucesso.")
        else:
            print("❌ Botão 'Busca' não encontrado.")

    # ── TESTE 8: detectar popup nenhum item ──────────────────
    elif escolha == "8":
        print("🔍 Verificando se o popup 'Nenhum item encontrado' está visível...")
        encontrado = auto_ocr.detectar_popup_nenhum_item()
        if encontrado:
            print("✅ Popup DETECTADO na tela.")
        else:
            print("ℹ️  Popup NÃO detectado (normal se não fez uma busca sem resultado).")

    # ── TESTE 9: fechar popup nenhum item ────────────────────
    elif escolha == "9":
        print("🔍 Tentando fechar o popup 'Nenhum item encontrado'...")
        ok = auto_ocr.fechar_popup_nenhum_item(pausar=1.0)
        if ok:
            print("✅ Popup fechado com sucesso.")
        else:
            print("ℹ️  Popup não estava visível para fechar.")

    # ── TESTE 10: selecionar linha com saldo ─────────────────
    elif escolha == "10":
        valor = input("   Digite a quantidade N8N para buscar na grade: ").strip()
        try:
            qtde = float(valor.replace(',', '.'))
        except ValueError:
            print("❌ Quantidade inválida.")
            continue

        print(f"🔍 Buscando linha com saldo >= {qtde} na grade inferior...")
        selecao = auto_ocr.selecionar_linha_com_saldo_por_qtde(
            x_qtde_header=X_QTDE_HEADER,
            y_qtde_header=Y_QTDE_HEADER,
            quantidade_n8n=qtde,
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
        if selecao["ok"]:
            print(f"✅ Linha encontrada e selecionada!")
            print(f"   idx={selecao['linha_index']} | qtde={selecao['qtde_lida']} | tipo={selecao['tipo_escolha']}")
        else:
            print(f"❌ Falha: {selecao['motivo']}")
            print(f"   Grade lida: {selecao.get('lista_grade')}")

    # ── TESTE 11: clicar seta para subir item ────────────────
    elif escolha == "11":
        print("🔍 Clicando na seta para subir item para a grade superior (670, 430)...")
        print("⚠️  ATENÇÃO: Isso vai subir o item atualmente selecionado na grade inferior!")
        confirm = input("   Confirma? (s/n): ").strip().lower()
        if confirm == 's':
            auto_ocr.clicar_coordenadas_fixas(670, 430, tipo_clique='single', pausar=0.8)
            print("✅ Clique executado.")
        else:
            print("⚠️  Cancelado.")

    # ── TESTE 12: editar Qtde na grade superior ───────────────
    elif escolha == "12":
        valor = input("   Digite a quantidade para editar na grade superior: ").strip()
        try:
            qtde = float(valor.replace(',', '.'))
        except ValueError:
            print("❌ Quantidade inválida.")
            continue

        print(f"🔍 Detectando última linha e editando Qtde. com '{valor}'...")
        res = auto_ocr.editar_qtde_ultimo_item_com_end(
            quantidade_n8n=qtde,
            salvar_debug_detecao=True  # salva debug_destaque.png para inspeção
        )
        if res["ok"]:
            print(f"✅ Qtde editada: '{res['qtde_colada']}' | y_detectado={res['y_rel_detectado']}")
            print(f"   Segmento local: {res['segmento_local']} | Score escuro: {res['score_escuro']:.3f}")
        else:
            print(f"❌ Falha: {res['motivo']}")

    # ── TESTE 13: detectar linha destacada por pixels ─────────
    elif escolha == "13":
        print("🔍 Detectando linha destacada por análise de pixels...")
        print("   Região: (80, 309, 762, 90)")
        det = auto_ocr.detectar_y_linha_destacada_por_pixels(
            regiao=(80, 309, 762, 90),
            limiar_escuro=120,
            dark_frac_min=0.55,
            min_altura_px=8,
            salvar_debug=True,
            nome_debug="debug_destaque_teste.png"
        )
        if det["ok"]:
            print(f"✅ Linha destacada detectada!")
            print(f"   y_rel={det['y_rel']} | segmento={det['segmento']} | score={det['score_escuro']:.3f}")
            print("   📁 Debug salvo em: debug_destaque_teste.png")
        else:
            print(f"❌ Não detectou linha destacada. Motivo: {det['motivo']}")
            if 'info' in det:
                print(f"   Info: {det['info']}")
            print("   💡 Selecione um item na grade superior antes de rodar este teste.")

    # ── TESTE 14: editar Valor Unitário ──────────────────────
    elif escolha == "14":
        y_val = input("   Digite o Y relativo da linha (ou deixe vazio para usar 350): ").strip()
        y_rel = int(y_val) if y_val.isdigit() else 350

        valor = input("   Digite o Valor Unitário para editar (ex: 2,5400000): ").strip()
        if not valor:
            print("⚠️  Nenhum valor digitado, pulando.")
            continue

        print(f"🔍 Clicando na coluna Valor Unitário (x=832, y={y_rel}) e colando '{valor}'...")
        res = auto_ocr.editar_valor_unitario_na_linha(
            valor_unitario_n8n=valor,
            y_rel_click=y_rel
        )
        if res["ok"]:
            print(f"✅ Valor Unitário editado: '{res['vunit_colado']}'")
        else:
            print(f"❌ Falha: {res['motivo']}")

    # ── TESTE 15: listar textos OCR tela inteira ─────────────
    elif escolha == "15":
        print("🔍 Executando OCR na tela inteira...")
        auto_ocr.listar_todos_textos(confianca_minima=30)

    # ── TESTE 16: listar textos OCR na região Qtde ───────────
    elif escolha == "16":
        print(f"🔍 Executando OCR na região REGIAO_QTDE: {REGIAO_QTDE}...")
        auto_ocr.listar_texto_regiao(confianca_minima=5, regiao=REGIAO_QTDE)

    else:
        print(f"⚠️  Opção '{escolha}' não reconhecida.")

print("\n" + "=" * 60)
print("🏁 Sessão de testes encerrada.")
print("=" * 60)
