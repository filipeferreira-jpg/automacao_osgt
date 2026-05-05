# login_sistema.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException 
from pathlib import Path
import time

# ─── FUNÇÃO HELPER ────────────────────────────────────────
def aguardar_novo_download_ica(arquivos_antes: set, timeout=60, pasta=None):
    """
    Aguarda um arquivo .ica NOVO aparecer na pasta Downloads.
    Compara com o snapshot feito ANTES do clique que dispara o download.
    Retorna o Path do arquivo novo quando encontrado, ou None se timeout.
    """
    pasta = pasta or (Path.home() / "Downloads")
    inicio = time.time()

    print("⏳ Aguardando download do arquivo .ica...")

    while time.time() - inicio < timeout:
        arquivos_atuais = set(pasta.glob("*.ica"))

        # Filtra apenas arquivos que NÃO existiam antes do clique
        arquivos_novos = arquivos_atuais - arquivos_antes

        # Ignora arquivos que ainda estão sendo baixados (.crdownload)
        arquivos_completos = [
            f for f in arquivos_novos
            if not pasta.joinpath(f.stem + ".crdownload").exists()
        ]

        if arquivos_completos:
            arquivo = max(arquivos_completos, key=lambda x: x.stat().st_mtime)
            print(f"✅ Novo download concluído: {arquivo.name}")
            return arquivo

        time.sleep(1)

    print("❌ Timeout: nenhum arquivo .ica novo encontrado!")
    return None

# ─── CONFIGURAÇÃO ─────────────────────────────────────────
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 20)

# abrindo o site
#driver.get("https://gtm-latam-uat.onesourcetax.com/module-selection/387/login") #URL do OSGT PHINIA -- TESTES
driver.get("https://gtm-latam.onesourcetax.com/module-selection/387/login") #URL do OSGT PHINIA - PRODUÇÃO
time.sleep(3)  # aguarda 10 segundos para a próxima etapa

# ─── LOGIN ─────────────────────────────────────────────────
#campo_user = driver.find_element(By.XPATH, '//*[@id="username"]')
campo_user = wait.until(EC.visibility_of_element_located((By.ID, "username")))
# preencher o campo de usuário
campo_user.clear()
#campo_user.send_keys("PJ4TLJ") # LOGIN NATHALIA
campo_user.send_keys("FJMDNL") # LOGIN KARINA
#campo_user.send_keys("PZJQ9S") # user PHINIA TESTE
#campo_user.send_keys("HJ2J7R") # user PRODUCAO PHINIA

#campo_pw = driver.find_element(By.XPATH, '//*[@id="password"]')
campo_pw = wait.until(EC.visibility_of_element_located((By.ID, "password")))
# preencher o campo de senha 
campo_pw.clear()
campo_pw.send_keys("Josafa2026abc@") # LOGIN KARINA
#campo_pw.send_keys("Nathi2027!@#") # login nathalia
#campo_pw.send_keys("renata01") # user PHINIA TESTE
#campo_pw.send_keys("Start@DT1oj13") # user PRODUCAO PHINIA
time.sleep(3)  # aguarda 3 segundos para a próxima etapa

# clicar no botão de login
# xpath do botão de login - //*[@id="submit-btn"]
#botao_login = driver.find_element(By.XPATH, '//*[@id="submit-btn"]')
botao_login = wait.until(EC.element_to_be_clickable((By.ID, "submit-btn")))
botao_login.click()
time.sleep(5)  # aguarda 10 segundos para a próxima etapa

# botão sistema -
botao_sistema = wait.until(EC.element_to_be_clickable(
    (By.XPATH, "//a[contains(@class,'module-box')]//span[@class='title' and normalize-space()='ONESOURCE Global Trade']/ancestor::a[1]")
    #(By.XPATH, '//img[@alt="OSGT_QA"]/parent::a[@class="storeapp-details-link"]') #- elemento clicável anterior, usado no ambiente de teste
))
handles_antes = driver.window_handles
botao_sistema.click()
time.sleep(10)  # aguarda 10 segundos para a próxima etapa

# ─── SNAPSHOT DOS .ICA EXISTENTES ANTES DO CLIQUE ────────
# Feito ANTES de clicar no app_element que dispara o download.
# Assim só consideramos como "novo" o que aparecer depois daqui.
pasta_downloads = Path.home() / "Downloads"
icas_antes_do_clique = set(pasta_downloads.glob("*.ica"))
print(f"📁 {len(icas_antes_do_clique)} arquivo(s) .ica já existiam na pasta (serão ignorados)")

try:
    # Aguarda nova janela aparecer
    wait.until(lambda d: len(d.window_handles) > len(handles_antes))

    # Troca para nova aba
    nova_aba = (set(driver.window_handles) - set(handles_antes)).pop()
    driver.switch_to.window(nova_aba)

    # ADICIONE: Aguarda o body da nova página carregar
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # OU aguarda um elemento específico que indica que a página carregou
    # wait.until(EC.presence_of_element_located((By.CLASS_NAME, "storeapp-details-link")))

    # Pequena pausa para JS executar (opcional mas recomendado)
    time.sleep(1)

    # Agora localiza e clica no elemento
    app_element = wait.until(EC.element_to_be_clickable(
        #(By.XPATH, '//img[@alt="OSGT_QA"]/parent::a[@class="storeapp-details-link"]') #PHINIA TESTE
        (By.XPATH, '//*[@id="home-screen"]/div[2]/section[5]/div[5]/div/ul/li/a[2]') #PHINIA PROD
    ))

    driver.execute_script("arguments[0].click();", app_element)
    print("Elemento clicado com sucesso!")

except TimeoutException:
    print("Timeout: elemento não encontrado")
    print(f"URL atual: {driver.current_url}")
    driver.save_screenshot("erro_elemento.png")

except Exception as e:
    print(f"Erro: {type(e).__name__} - {str(e)}")

# ─── AGUARDA NOVO DOWNLOAD E SÓ ENTÃO ENCERRA ─────────────
# Passa o snapshot feito ANTES do clique para comparação.
# Só encerra quando um .ica NOVO (não existente antes) for detectado.
arquivo_ica = aguardar_novo_download_ica(
    arquivos_antes=icas_antes_do_clique,
    timeout=60
)

if not arquivo_ica:
    print("⚠️ Download do .ica não confirmado. Verifique manualmente.")
else:
    print(f"📄 Arquivo pronto para uso: {arquivo_ica.name}")

# Chrome só fecha aqui, depois de confirmar o download do novo .ica
driver.quit()
print("🔴 Chrome encerrado. Próxima etapa: executa_citrix.py")