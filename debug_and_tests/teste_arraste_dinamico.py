import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ============================================================
# SCRIPT DE TESTE: Arraste Dinâmico de Coluna via OCR
# Testa a localização e o arraste dinâmico sem conectar ao N8N
# ============================================================
import time
import sys
from models.automacao_cliques import AutomacaoOCR

def testar_arraste_dinamico():
    print("--- Inicializando AutomacaoOCR na janela 'Import' ---")
    auto_ocr = AutomacaoOCR('Import')
    
    # 1. Garante que a janela está focada e visível
    print("-> Focando na janela do ERP...")
    if not auto_ocr.captura.janela_atual:
        print("[-] Janela principal nao encontrada. Certifique-se de que o ERP esta aberto na tela 'Macro Item'.")
        sys.exit(1)
        
    auto_ocr.captura.focar_janela()
    time.sleep(1.0)
    auto_ocr.clicar_coordenadas_multiclick(908, 392, clicks=4, intervalo=0.5, pausar=0.5) #coordenadas 1024x768

    print("\n" + "=" * 60)
    print("ETAPA 1: DETECCAO DINAMICA DOS CABECALHOS")
    print("=" * 60)
    
    # Regiões de busca para o cabeçalho 'Qtde.' (baseadas na resolução 1024x768)
    # Formato: (x_rel, y_rel, largura, altura)
    # Cobrimos uma faixa horizontal de X=200 a X=900 para abranger toda a largura das grades
    regiao_superior = (200, 275, 700, 45) # Região aproximada do cabeçalho da Tabela Superior (Y ≈ 300)
    regiao_inferior = (200, 500, 700, 45) # Região aproximada do cabeçalho da Tabela Inferior (Y ≈ 525)
    
    # Buscamos a palavra "Qtde." com similaridade menor para tolerar leitura sem o ponto
    print("-> Procurando 'Qtde.' na Tabela Superior (Itens da Fatura)...")
    res_sup = auto_ocr.encontrar_texto(
        texto_busca="Qtde", 
        confianca_minima=10, 
        regiao=regiao_superior,
        similaridade_minima=0.55
    )
    
    print("\n-> Procurando 'Qtde.' na Tabela Inferior (Itens da Ordem)...")
    res_inf = auto_ocr.encontrar_texto(
        texto_busca="Qtde", 
        confianca_minima=10, 
        regiao=regiao_inferior,
        similaridade_minima=0.55
    )
    
    print("\n" + "=" * 60)
    print("ETAPA 2: CALCULO E ANALISE DE COORDENADAS")
    print("=" * 60)
    
    x_divisoria_sup = None
    y_sup = 300 # fallback
    
    if res_sup:
        x_centro = res_sup['x_rel']
        y_sup = res_sup['y_rel']
        # A divisória esquerda da coluna 'Qtde.' (que divide com Agrupamento) 
        # fica aproximadamente 40 pixels para a esquerda do centro do texto.
        x_divisoria_sup = x_centro - 40
        print(f"[+] TABELA SUPERIOR:")
        print(f"   - Centro do texto 'Qtde.': ({x_centro}, {y_sup})")
        print(f"   - Divisoria esquerda calculada: X = {x_divisoria_sup}")
    else:
        print("[-] TABELA SUPERIOR: Nao foi possivel detectar o cabecalho 'Qtde.' via OCR.")
        print("   -> Dica: Verifique se a tabela superior esta visivel na tela e sem popups cobrindo.")
        
    if res_inf:
        x_centro = res_inf['x_rel']
        y_inf = res_inf['y_rel']
        # A divisória direita da coluna 'Qtde.' (onde arrastamos para alargar a coluna)
        # fica aproximadamente 40 pixels para a direita do centro do texto.
        x_divisoria_inf = x_centro + 40
        print(f"\n[+] TABELA INFERIOR:")
        print(f"   - Centro do texto 'Qtde.': ({x_centro}, {y_inf})")
        print(f"   - Divisoria direita calculada: X = {x_divisoria_inf}")
    else:
        print("\n[-] TABELA INFERIOR: Nao foi possivel detectar o cabecalho 'Qtde.' via OCR.")
        
    print("\n" + "=" * 60)
    print("ETAPA 3: EXECUCAO DO ARRASTE DE TESTE")
    print("=" * 60)
    
    if x_divisoria_sup:
        # Ponto de destino: arrastamos 120 pixels para a esquerda para estreitar a coluna "Agrupamento"
        x_destino_sup = x_divisoria_sup - 150
        
        print(f"-> Iniciando teste de arraste na Tabela Superior:")
        print(f"   Origem:  ({x_divisoria_sup}, {y_sup}) [Divisoria calculada]")
        print(f"   Destino: ({x_destino_sup}, {y_sup}) [Estreitando a coluna]")
        print("   (Observe se o mouse clica exatamente na divisoria e move a coluna)")
        
        time.sleep(1.0)
        
        sucesso = auto_ocr.arrastar_coluna_quantidade(
            x_inicio_rel=x_divisoria_sup,
            y_inicio_rel=y_sup,
            x_fim_rel=x_destino_sup,
            y_fim_rel=y_sup,
            duracao_arraste=0.4,
            pausar=1.0
        )
        
        if sucesso:
            print("\n[+] Comando de arraste enviado com sucesso!")
            print("   Se a coluna se moveu, a calibracao de 40 pixels esta correta.")
            print("   Se o mouse clicou fora (para esquerda ou direita da divisoria), ajustaremos o offset.")
        else:
            print("\n[-] Ocorreu um erro fisico na execucao do arraste.")
    else:
        print("[>] Teste de arraste cancelado porque o cabecalho superior nao foi localizado.")

if __name__ == "__main__":
    testar_arraste_dinamico()
