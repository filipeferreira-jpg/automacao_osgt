import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ============================================================
# TESTE DE DELAYS - ENCONTRAR O DELAY IDEAL
# ============================================================
from models.automacao_cliques import AutomacaoOCR
import time

print("="*60)
print("🧪 TESTE DE DELAYS")
print("="*60)

auto = AutomacaoOCR('Import')

# Testa diferentes delays
delays = [0.5, 0.7, 0.8, 1.0, 1.2, 1.5]

for delay in delays:
    print(f"\n{'='*60}")
    print(f"🧪 Testando delay: {delay}s ({int(delay*1000)}ms)")
    print("="*60)

    # Preenche o campo
    auto.preencher_campo_por_coordenadas(
        x_rel=342,
        y_rel=494,
        valor=f'TEST{int(delay*100)}',  # Ex: TEST15 para 0.15s
        delay=delay,
        limpar_antes=True
    )

    time.sleep(2)

    # Pergunta se duplicou
    print(f"\n❓ O texto duplicou com delay={delay}s? (s/n): ", end='')
    resposta = input().lower()

    if resposta == 'n':
        print(f"\n✅ DELAY IDEAL ENCONTRADO: {delay}s ({int(delay*1000)}ms)")
        print(f"\nAtualize no código:")
        print(f"  time.sleep({delay})  # Entre cada caractere")
        break
    else:
        print(f"⚠️  Ainda duplicou, tentando delay maior...")

print("\n" + "="*60)
print("✅ Teste de delays concluído")
print("="*60)
