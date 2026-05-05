# ============================================================
# CÉLULA: ORQUESTRADOR PRINCIPAL (main.py)
# ============================================================
import subprocess
import sys
import time

print("="*60)
print("🚀 INICIANDO FLUXO DE AUTOMAÇÃO PRINCIPAL")
print("="*60)

# ─────────────────────────────────────────────────────────
# 1. Executa login_sistema.py
# ─────────────────────────────────────────────s────────────
print("\n📍 EXECUTANDO: login_sistema.py")
print("-"*60)
try:
    resultado_login = subprocess.run(
        [sys.executable, "login_sistema.py"],
        capture_output=False,  # Mostra o output em tempo real no terminal
        text=True,
        check=True             # Levanta exceção se o script retornar erro
    )
    print("✅ login_sistema.py concluído com sucesso!")
except subprocess.CalledProcessError as e:
    print(f"❌ login_sistema.py falhou com erro: {e}")
    print(f"   Stderr: {e.stderr}")
    sys.exit(1) # Sai do programa principal com código de erro
except Exception as e:
    print(f"❌ Erro inesperado ao executar login_sistema.py: {e}")
    sys.exit(1)

# ─────────────────────────────────────────────────────────
# 2. Executa executa_citrix.py
# ─────────────────────────────────────────────────────────
print("\n📍 EXECUTANDO: executa_citrix.py")
print("-"*60)
try:
    resultado_citrix = subprocess.run(
        [sys.executable, "executa_citrix.py"],
        capture_output=False,
        text=True,
        check=True
    )
    print("✅ executa_citrix.py concluído com sucesso!")
except subprocess.CalledProcessError as e:
    print(f"❌ executa_citrix.py falhou com erro: {e}")
    print(f"   Stderr: {e.stderr}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erro inesperado ao executar executa_citrix.py: {e}")
    sys.exit(1)

# Pequena pausa para o Citrix Workspace iniciar e a janela 'Módulos' aparecer
print("\n⏳ Aguardando o Citrix Workspace iniciar e a janela 'Módulos' aparecer...")
time.sleep(15) # Ajuste este tempo conforme a velocidade de inicialização do Citrix na sua máquina

# ─────────────────────────────────────────────────────────
# 3. Executa automation_rascunho.py
# ─────────────────────────────────────────────────────────
print("\n📍 EXECUTANDO: automation_rascunho.py")
print("-"*60)
try:
    resultado_automation = subprocess.run(
        [sys.executable, "automation_rascunho.py"],
        capture_output=False,
        text=True,
        check=True
    )
    print("✅ automation_rascunho.py concluído com sucesso!")
except subprocess.CalledProcessError as e:
    print(f"❌ automation_rascunho.py falhou com erro: {e}")
    print(f"   Stderr: {e.stderr}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erro inesperado ao executar automation_rascunho.py: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("🎉 FLUXO DE AUTOMAÇÃO PRINCIPAL CONCLUÍDO COM SUCESSO!")
print("="*60)