#%pip install selenium

# Prepara o webdriver
def preparar_driver(path_projeto):

    import sys
    import os
    import time

    # Checa se o chromedriver existe, caso não exista, encerra
    if not os.path.isfile(f'{path_projeto}/chromedriver.exe'):
        print('Chromedriver não encontrado...')
        print('1) Faça download do chromedriver no endereço abaixo')
        print('https://chromedriver.chromium.org/downloads' + '\n')
        print('2) Copie o arquivo "chromedriver.exe" para a pasta do projeto')
        time.sleep(10)
        sys.exit()

    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('prefs', 
        {
            "plugins.always_open_pdf_externally": True,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            'download.default_directory': os.path.join(path_projeto, 'arquivos')
        }
    )

    driver = webdriver.Chrome(service=Service(f'{path_projeto}/chromedriver.exe'), options=chrome_options)
    driver.minimize_window()

    login_url = 'https://painelprc.trf5.jus.br/painelprc/auth'
    driver.get(login_url)

    return driver

# Acessar a página de pesquisa
def preparar_pesquisa(driver):

    import time

    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By

    driver.maximize_window()
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)
    driver.find_element(By.ID, 'cardextratodemo').find_element(By.TAG_NAME, 'button').click()

    time.sleep(3)
    driver.find_element(By.ID, 'form:numeroRequisitorio').clear()

# Download de cada demonstrativo
def download_demonstrativo(driver, path_arquivos, requisitorio):
    
    import os
    import time

    from selenium.webdriver.common.by import By

    print(f'{requisitorio} ... ', end='')

    nome_arquivo = f'{path_arquivos}/{requisitorio}.pdf'
    if os.path.isfile(nome_arquivo): 
        print('já existe')
        return 

    driver.find_element(By.ID, 'form:numeroRequisitorio').clear()
    driver.find_element(By.ID, 'form:numeroRequisitorio').send_keys(requisitorio)
    driver.find_element(By.CSS_SELECTOR, '#form\:idTipoRequisitorio > tbody > tr > td:nth-child(3) > div').click()

    time.sleep(1)
    driver.find_element(By.ID, 'form:j_idt65').click()
    time.sleep(3)

    tabela_resultados = driver.find_element(By.ID, 'outroForm:listaextratoXXT_data')
    qtd_celulas_tabela_resultado = len(tabela_resultados.find_elements(By.TAG_NAME, 'td'))
    if qtd_celulas_tabela_resultado == 1: 
        print('não encontrado')
        return
    
    driver.find_element(By.ID, 'outroForm:listaextratoXXT:0:btnpdf').click()
    time.sleep(3)

    nome_padrao =  path_arquivos.replace("/", "\\") + '\\PRC'

    os.rename(nome_padrao, nome_arquivo)

    print('baixado com sucesso')
    return 

# Enter para continuar e Esc para cancelar
def aguardar_usuario():
    
    import sys
    import msvcrt
    
    while True:
        key = msvcrt.getch()
        if key == b'\r':  # Enter key
            break
        elif key == b'\x1b':  # Esc key
            sys.exit()

# Função para ler arquivo
def ler_arquivo(nome_arquivo):
    import csv, os, time, sys

    # Checa se o arquivo CSV existe, caso não exista, encerra
    if not os.path.isfile(nome_arquivo): 
        print('Arquivo requisitorios.csv não encontrado...')
        time.sleep(3)
        sys.exit()

    lista = []
    with open(nome_arquivo, 'r', encoding='UTF-8') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            lista.append(row[0])

    return lista

# Função para salvar arquivo
def salvar(rows, arquivo_saida):
    import csv
    with open(arquivo_saida, 'a',  encoding='UTF-8',  newline='') as f:
        writer = csv.writer(f, delimiter =';')
        for row in rows:
            writer.writerow(row)

def log_on_google(client, script, text):

    import requests as re
    payload = {
        'entry.2051406178': client,
        'entry.1662748811': script,
        'entry.1806349460': text,
        'hud': True,
        'fvv': '1',
        'pageHistory': '0',
        'fbzx': '-5127016485562115995'
    }

    form_url = 'https://docs.google.com/forms/u/0/d/e/1FAIpQLSd6GXzvOPJ23nVShkFiIO5kO1ZSKKJKHqP4C0j-X5yPJ1gyng/formResponse'
    response = re.post(url=form_url, data=payload)
    return response.status_code

def main():
    
    import os
    import time
    import sys

    path_projeto = os.path.dirname(os.path.abspath(sys.argv[0]))
    
    # Lê o arquivo
    path_arquivo = os.path.join(path_projeto, 'requisitorios.csv')
    lista = ler_arquivo(path_arquivo)
    print('\n' + '='*70 + '\n')
    print(f'Sua lista possuí {len(lista)} requisitórios.')  

    # Checa se o diretório existe, caso não exista, cria o diretório
    path_arquivos = os.path.join(path_projeto, 'arquivos')
    if not os.path.exists(path_arquivos): os.makedirs(path_arquivos)
    print(f'Seus arquivos serão salvos na pasta abaixo:' + '\n')
    print(path_arquivos)
    print('='*70 + '\n')

    # Abre o navegador e pede para fazer login
    driver = preparar_driver(path_projeto)
    print('='*70 + '\n')
    print('Faça login no PJE...' + '\n')
    print('Após fazer login, aperte Enter para continuar ou Esc para cancelar' + '\n\n')

    aguardar_usuario()
    preparar_pesquisa(driver)

    errors = []
    i = 0

    print('Buscando requisitórios:' + '\n')
    for requisitorio in lista:
        time.sleep(0.5) # Delay entre iterações
        print(f'{i+1} de {len(lista)} - ', end='')
        try:
            download_demonstrativo(driver, path_arquivos, requisitorio)
            log_on_google('Martorelli', 'Extratos de Pagamento', requisitorio)
        except Exception as e:
            erro = [requisitorio, type(e).__name__] # Salva item com erro e a descrição do erro
            salvar(erro, 'erros.csv')
            errors.append(erro)
        
        i+=1

if __name__ == '__main__':
    main()