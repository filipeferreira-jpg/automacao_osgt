import os
import subprocess
from pathlib import Path
import time

def executar_ultimo_ica():
    downloads = Path.home() / "Downloads"

    # Lista todos os arquivos .ica
    arquivos_ica = list(downloads.glob("*.ica"))

    if not arquivos_ica:
        print("Nenhum arquivo .ica encontrado na pasta Downloads!")
        return False

    # Pega o mais recente baseado na data de modificação
    arquivo_recente = max(arquivos_ica, key=lambda x: x.stat().st_mtime)

    print(f"Executando: {arquivo_recente.name}")

    # Executa o arquivo .ica
    os.startfile(str(arquivo_recente))
    return True

# Usar
executar_ultimo_ica()