import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sys
import time
from models.automacao_cliques import AutomacaoOCR

TITULO_JANELA = "ONESOURCE"  # ajuste para o título exato da sua janela

# ─────────────────────────────────────────
# CONFIGURAÇÃO — ajuste esses valores
# ─────────────────────────────────────────
REGIAO_QTDE     = (720, 540, 80, 90)   # (x, y, largura, altura) da coluna Qtde.
ALTURA_LINHA    = 18
MARGEM_SUPERIOR = 0
MARGEM_INFERIOR = 0

PREPROCESSING_CONFIG = {
    'grayscale'            : True,
    'amplify_factor'       : 2,
    'contrast'             : 2.0,
    'threshold'            : 140,
    'whitelist'            : '0123456789,.',
    'psm'                  : 7,
    'debug_filename_prefix': 'debug_qtde_ocr'
}
# ─────────────────────────────────────────

def main():
    print("=" * 60)
    print("DEBUG: leitura faixa a faixa da coluna Qtde.")
    print("=" * 60)

    auto = AutomacaoOCR(titulo_janela=TITULO_JANELA)

    if not auto.captura.janela_atual:
        print("❌ Janela não encontrada. Verifique TITULO_JANELA.")
        sys.exit(1)

    # ── 1. Salva imagem com as faixas desenhadas ──────────────
    print("\n[1] Gerando imagem de debug das faixas...")
    auto.debug_faixas_coluna_qtde(
        regiao_qtde=REGIAO_QTDE,
        altura_linha=ALTURA_LINHA,
        margem_superior=MARGEM_SUPERIOR,
        margem_inferior=MARGEM_INFERIOR,
        nome_arquivo='debug_faixas_qtde.png'
    )
    print("    → Abra 'debug_faixas_qtde.png' e verifique se cada faixa")
    print("      cobre exatamente uma linha da grade.")

    # ── 2. Lê faixa a faixa com imagens de debug por linha ───
    print("\n[2] Lendo faixa a faixa com OCR + debug de imagem...")

    faixas = auto._gerar_faixas_linhas_coluna(
        regiao_qtde=REGIAO_QTDE,
        altura_linha=ALTURA_LINHA,
        margem_superior=MARGEM_SUPERIOR,
        margem_inferior=MARGEM_INFERIOR
    )

    print(f"    Total de faixas geradas: {len(faixas)}")

    resultados = []

    for idx, faixa in enumerate(faixas, start=1):
        x, y, w, h = faixa
        print(f"\n{'─'*50}")
        print(f"  Linha {idx} | faixa={faixa}")

        # Salva imagem individual da faixa (original + processada)
        config_debug = dict(PREPROCESSING_CONFIG)
        config_debug['debug_filename_prefix'] = f'debug_linha_{idx:02d}'

        candidatos = auto._extrair_candidatos_ocr_da_faixa(
            regiao_faixa=faixa,
            confianca_minima=5,
            preprocessing_config=config_debug
        )

        if candidatos:
            melhor = sorted(
                candidatos,
                key=lambda c: (c['conf'], len(str(c['texto']))),
                reverse=True
            )[0]
            print(f"  ✅ Melhor candidato: texto='{melhor['texto']}' | valor={melhor['valor']} | conf={melhor['conf']}")
            resultados.append({'linha': idx, 'faixa': faixa, 'valor': melhor['valor'], 'candidatos': candidatos})
        else:
            print(f"  ❌ Sem candidatos válidos — verifique 'debug_linha_{idx:02d}_original.png'")
            resultados.append({'linha': idx, 'faixa': faixa, 'valor': None, 'candidatos': []})

        # Pausa para não sobrecarregar o OCR
        time.sleep(0.1)

    # ── 3. Resumo final ───────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("RESUMO:")
    print(f"{'=' * 60}")

    lista_lida = []
    for r in resultados:
        status = f"{r['valor']}" if r['valor'] is not None else "❌ NÃO LIDO"
        print(f"  Linha {r['linha']:02d} | faixa y={r['faixa'][1]} | valor={status}")
        if r['valor'] is not None:
            lista_lida.append(r['valor'])

    print(f"\nLista final lida: {lista_lida}")
    print(f"\nArquivos de debug gerados:")
    print(f"  - debug_faixas_qtde.png        → faixas sobrepostas na tela")
    for r in resultados:
        print(f"  - debug_linha_{r['linha']:02d}_original.png  → recorte bruto da linha {r['linha']}")
        print(f"  - debug_linha_{r['linha']:02d}_processada.png → após pré-processamento")

    print(f"\n{'=' * 60}")
    print("PRÓXIMOS PASSOS:")
    print("  1. Abra 'debug_faixas_qtde.png' — as faixas estão alinhadas com as linhas?")
    print("  2. Abra 'debug_linha_03_original.png' — o valor 740 está visível?")
    print("  3. Abra 'debug_linha_03_processada.png' — o texto ficou legível após o filtro?")
    print("  4. Se o 740 estiver cortado, ajuste REGIAO_QTDE ou ALTURA_LINHA.")
    print("  5. Se o texto estiver ilegível, ajuste contrast/threshold no PREPROCESSING_CONFIG.")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()