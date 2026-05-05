"""
Mapeia múltiplos elementos em sequência
"""
import sys
from pathlib import Path

print("sys.path[0]:", sys.path[0])
print("project root exists?:", (Path(sys.path[0]).parent / "models").exists())

from models.captura_tela import CapturaTela
import pyautogui
import time

def mapear_elementos(titulo_janela, elementos):
    """
    Mapeia vários elementos em sequência

    Args:
        titulo_janela: Título da janela
        elementos: Lista de nomes dos elementos a mapear

    Returns:
        Dict com coordenadas de cada elemento
    """
    print("="*60)
    print(f"🎯 MAPEANDO ELEMENTOS NA JANELA '{titulo_janela}'")
    print("="*60)

    captura = CapturaTela()

    if not captura.encontrar_janela(titulo_janela):
        print(f"❌ Janela '{titulo_janela}' não encontrada")
        return {}

    captura.focar_janela()
    coordenadas = {}

    for i, elemento in enumerate(elementos, 1):
        print(f"\n{'='*60}")
        print(f"📍 ELEMENTO {i}/{len(elementos)}: {elemento}")
        print("="*60)
        print("Posicione o mouse sobre o elemento e aguarde 5 segundos...\n")

        for seg in range(5, 0, -1):
            print(f"⏱️  {seg}...")
            time.sleep(1)

        # Captura posição
        x_abs, y_abs = pyautogui.position()
        x_rel = x_abs - captura.janela_atual.left
        y_rel = y_abs - captura.janela_atual.top

        coordenadas[elemento] = {
            'x_rel': x_rel,
            'y_rel': y_rel,
            'x_abs': x_abs,
            'y_abs': y_abs
        }

        print(f"\n✓ '{elemento}' mapeado: ({x_rel}, {y_rel})")

    # Mostra resumo
    print("\n" + "="*60)
    print("📊 RESUMO DAS COORDENADAS MAPEADAS:")
    print("="*60)

    for elemento, coords in coordenadas.items():
        print(f"\n{elemento}:")
        print(f"  x, y = captura.obter_posicao_absoluta({coords['x_rel']}, {coords['y_rel']})")

    print("\n" + "="*60)
    print("✅ MAPEAMENTO CONCLUÍDO!")
    print("="*60)

    return coordenadas


if __name__ == "__main__":
    # Exemplo: mapear botões na janela de Faturas
    elementos_mapear = [
        'Primeiro mapeamento - Botão +',
        'Segundo mapeamento - submenu Composição',
        'Terceiro mapeamento - Botão + para adicionar item',
        'sobrando'
    ]

    coords = mapear_elementos('Import', elementos_mapear)
