import requests
from bs4 import BeautifulSoup
import json
import time
import sqlite3
import os
import sys
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURAÇÕES GLOBAIS ---
DB_FOLDER_PATH = os.path.join(os.getcwd(), 'database')
DB_FILE = os.path.join(DB_FOLDER_PATH, 'brasileirao.db')
ID_COMPETICAO_CBF = 12606
ANO_COMPETICAO = 2024 # Usando 2024 para garantir dados completos e estáveis
TOTAL_RODADAS = 38
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

# MAPEAMENTO CRUCIAL E CORRIGIDO (O SEU MAPA):
MAPA_NOMES_EXTERNOS_PARA_CBF = {
    "Atlético-MG": "Atlético Mineiro Saf", "RB Bragantino": "Red Bull Bragantino",
    "São Paulo": "São Paulo", "Flamengo": "Flamengo", "Corinthians": "Corinthians",
    "Vasco da Gama": "Vasco da Gama S.a.f.", "Vasco": "Vasco da Gama S.a.f.",
    "Bahia": "Bahia", "Vitória": "Vitória", "Fortaleza": "Fortaleza Ec Saf",
    "Ceará": "Ceará", "Mirassol": "Mirassol", "Sport Recife": "Sport", "Juventude": "Juventude",
    "Grêmio": "Grêmio", "Palmeiras": "Palmeiras", "Fluminense": "Fluminense",
    "Santos": "Santos Fc", "Botafogo": "Botafogo", "Internacional": "Internacional",
    "Cruzeiro": "Cruzeiro Saf",
}

# --- FUNÇÕES DO BANCO DE DADOS ---
def criar_banco_de_dados():
    os.makedirs(DB_FOLDER_PATH, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS times (id INTEGER PRIMARY KEY, nome TEXT NOT NULL UNIQUE, url_escudo TEXT)')
    cursor.execute('''CREATE TABLE IF NOT EXISTS atletas (id INTEGER PRIMARY KEY, apelido TEXT NOT NULL, cartoes_amarelos INTEGER DEFAULT 0, cartoes_vermelhos INTEGER DEFAULT 0, rodada_ultimo_vermelho INTEGER DEFAULT 0, rodada_suspensao_amarelo INTEGER DEFAULT 0, time_id INTEGER, FOREIGN KEY (time_id) REFERENCES times (id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS jogos_finalizados (id_jogo INTEGER PRIMARY KEY, rodada INTEGER NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS partidas (id_jogo INTEGER PRIMARY KEY, rodada INTEGER NOT NULL, data TEXT, hora TEXT, local TEXT, mandante_nome TEXT, mandante_url_escudo TEXT, mandante_gols TEXT, visitante_nome TEXT, visitante_url_escudo TEXT, visitante_gols TEXT)''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estatisticas_time (
            time_id INTEGER PRIMARY KEY, posicao INTEGER, pontos INTEGER, ultimos_jogos TEXT,
            media_cartoes_amarelos REAL, total_cartoes_vermelhos INTEGER, media_escanteios REAL,
            FOREIGN KEY (time_id) REFERENCES times (id)
        )''')
    conn.commit()
    conn.close()
    print(f"Banco de dados verificado/criado em: {DB_FILE}")

def limpar_tabelas():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    print("Limpando dados antigos...")
    cursor.execute("DELETE FROM atletas"); cursor.execute("DELETE FROM times"); cursor.execute("DELETE FROM jogos_finalizados"); cursor.execute("DELETE FROM partidas"); cursor.execute("DELETE FROM estatisticas_time")
    conn.commit()
    conn.close()
    print("Tabelas limpas.")

def salvar_dados_no_banco(estatisticas_jogadores, times_info, jogos_finalizados_info, todas_as_partidas_info, estatisticas_times):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    print("\nSalvando novos dados no banco de dados...")
    for time_id, dados_time in times_info.items():
        cursor.execute('INSERT OR REPLACE INTO times (id, nome, url_escudo) VALUES (?, ?, ?)', (time_id, dados_time['nome'], dados_time['url_escudo']))
    for atleta_id, dados_atleta in estatisticas_jogadores.items():
        cursor.execute('INSERT OR REPLACE INTO atletas (id, apelido, cartoes_amarelos, cartoes_vermelhos, rodada_ultimo_vermelho, rodada_suspensao_amarelo, time_id) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                       (atleta_id, dados_atleta['nome'], dados_atleta['amarelos'], dados_atleta['vermelhos'], dados_atleta['rodada_ultimo_vermelho'], dados_atleta.get('rodada_suspensao_amarelo', 0), dados_atleta['time_id']))
    for jogo in jogos_finalizados_info:
        cursor.execute('INSERT OR REPLACE INTO jogos_finalizados (id_jogo, rodada) VALUES (?, ?)', (jogo['id_jogo'], jogo['rodada']))
    for jogo in todas_as_partidas_info:
        cursor.execute('''INSERT OR REPLACE INTO partidas (id_jogo, rodada, data, hora, local, mandante_nome, mandante_url_escudo, mandante_gols, visitante_nome, visitante_url_escudo, visitante_gols) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (jogo['id_jogo'], jogo['rodada'], jogo['data'], jogo['hora'], jogo['local'], jogo['mandante_nome'], jogo['mandante_url_escudo'], jogo['mandante_gols'], jogo['visitante_nome'], jogo['visitante_url_escudo'], jogo['visitante_gols']))
    if estatisticas_times:
        for time_id, stats in estatisticas_times.items():
            cursor.execute('''INSERT OR REPLACE INTO estatisticas_time (time_id, posicao, pontos, ultimos_jogos, media_cartoes_amarelos, total_cartoes_vermelhos, media_escanteios) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                           (time_id, stats.get('posicao'), stats.get('pontos'), stats.get('ultimos_jogos'), stats.get('media_amarelos', 0), stats.get('total_vermelhos', 0), stats.get('media_escanteios', 0)))
    conn.commit()
    conn.close()
    print("✅ Dados salvos/atualizados com sucesso.")

# --- FUNÇÕES DE COLETA ---
def buscar_dados_campeonato_completo(id_competicao, num_rodadas):
    estatisticas_jogadores, times_info = {}, {}
    jogos_finalizados_info, todas_as_partidas_info = [], []
    for i in range(1, num_rodadas + 1):
        url_rodada = f"https://www.cbf.com.br/api/proxy?path=/jogos/campeonato/{id_competicao}/rodada/{i}/fase"
        print(f"Buscando dados da Rodada {i}...")
        try:
            time.sleep(1)
            response = requests.get(url_rodada, headers=HEADERS, timeout=20)
            if response.status_code == 429: time.sleep(10); response = requests.get(url_rodada, headers=HEADERS, timeout=20)
            response.raise_for_status()
            dados_api = response.json()
            for grupo_de_jogos in dados_api.get('jogos', []):
                for jogo in grupo_de_jogos.get('jogo', []):
                    jogo_id = jogo.get('id_jogo')
                    if not jogo_id: continue
                    mandante = jogo.get('mandante', {}); visitante = jogo.get('visitante', {})
                    todas_as_partidas_info.append({'id_jogo': jogo_id, 'rodada': i, 'data': jogo.get('data'), 'hora': jogo.get('hora'), 'local': jogo.get('local'), 'mandante_nome': mandante.get('nome'), 'mandante_url_escudo': mandante.get('url_escudo'), 'mandante_gols': mandante.get('gols'), 'visitante_nome': visitante.get('nome'), 'visitante_url_escudo': visitante.get('url_escudo'), 'visitante_gols': visitante.get('gols')})
                    documentos = jogo.get('documentos')
                    if documentos and isinstance(documentos, list) and len(documentos) > 0:
                        jogos_finalizados_info.append({'id_jogo': jogo_id, 'rodada': i})
                    for time_info in [mandante, visitante]:
                        time_id = time_info.get('id')
                        if time_id and time_id not in times_info: times_info[time_id] = {'nome': time_info.get('nome'), 'url_escudo': time_info.get('url_escudo')}
                    for penalidade in jogo.get('penalidades', []):
                        if penalidade.get('tipo') == 'PENALIDADE':
                            if penalidade.get('atleta_camisa') is None: continue
                            atleta_id = int(penalidade.get('atleta_id', 0)); clube_id = int(penalidade.get('clube_id', 0)); atleta_apelido = penalidade.get('atleta_apelido')
                            if not all([atleta_id, clube_id, atleta_apelido]): continue
                            if atleta_id not in estatisticas_jogadores: 
                                estatisticas_jogadores[atleta_id] = {'nome': atleta_apelido, 'time_id': clube_id, 'amarelos': 0, 'vermelhos': 0, 'rodada_ultimo_vermelho': 0, 'rodada_suspensao_amarelo': 0}
                            
                            resultado = penalidade.get('resultado')
                            
                            if resultado == 'AMARELO':
                                estatisticas_jogadores[atleta_id]['amarelos'] += 1
                                if estatisticas_jogadores[atleta_id]['amarelos'] > 0 and estatisticas_jogadores[atleta_id]['amarelos'] % 3 == 0:
                                    estatisticas_jogadores[atleta_id]['rodada_suspensao_amarelo'] = i
                            elif resultado == 'VERMELHO':
                                estatisticas_jogadores[atleta_id]['vermelhos'] += 1
                                estatisticas_jogadores[atleta_id]['rodada_ultimo_vermelho'] = i
                            elif resultado == 'VERMELHO2AMARELO':
                                estatisticas_jogadores[atleta_id]['amarelos'] += 1
                                estatisticas_jogadores[atleta_id]['vermelhos'] += 1
                                estatisticas_jogadores[atleta_id]['rodada_ultimo_vermelho'] = i
                                if estatisticas_jogadores[atleta_id]['amarelos'] > 0 and estatisticas_jogadores[atleta_id]['amarelos'] % 3 == 0:
                                    estatisticas_jogadores[atleta_id]['rodada_suspensao_amarelo'] = i
        except Exception as e:
            print(f"   > Erro ao buscar rodada {i}: {e}. Pulando.")
            continue
    return estatisticas_jogadores, times_info, jogos_finalizados_info, todas_as_partidas_info

def buscar_classificacao_com_scraping(ano_competicao, times_info):
    print("\nBuscando dados de classificação via Web Scraping da CBF...")
    url_tabela = f"https://www.cbf.com.br/futebol-brasileiro/tabelas/campeonato-brasileiro/serie-a/{ano_competicao}"
    estatisticas_times = {}
    try:
        response = requests.get(url_tabela, headers=HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        container_tabela = soup.find('div', class_='styles_tableContent__dh0gO')
        if not container_tabela: return {}
        tabela = container_tabela.find('table')
        if not tabela: return {}
        linhas = tabela.find('tbody').find_all('tr')
        
        mapa_api_normalizado = {info['nome'].lower().replace(' saf', '').replace('s.a.f.', '').replace(' ec', '').replace(' cr', '').strip(): time_id for time_id, info in times_info.items()}
            
        for linha in linhas:
            celulas = linha.find_all('td')
            if len(celulas) < 13: continue
            posicao_tag = celulas[0].find('strong'); nome_time_tag = celulas[0].find('strong', class_=lambda c: c is None or 'styles' not in c)
            pontos_tag = celulas[1]; jogos_tag = celulas[2]; ultimos_jogos_container = celulas[12].find('div')
            if not all([posicao_tag, nome_time_tag, pontos_tag, jogos_tag, ultimos_jogos_container]): continue
            posicao = posicao_tag.text.strip(); nome_time_completo = nome_time_tag.text.strip(); pontos = pontos_tag.text.strip(); jogos_disputados = int(jogos_tag.text.strip())
            ultimos_jogos_svgs = ultimos_jogos_container.find_all('svg')
            ultimos_jogos_str = "".join(['V' if svg.find('circle')['fill'] == '#24C796' else 'E' if svg.find('circle')['fill'] == '#B7B7B7' else 'D' for svg in ultimos_jogos_svgs if svg.find('circle')])
            
            nome_site_normalizado = nome_time_completo.lower().replace(' saf', '').replace('s.a.f.', '').replace(' ec', '').replace(' cr', '').strip()
            time_id = mapa_api_normalizado.get(nome_site_normalizado)
            
            if time_id:
                estatisticas_times[time_id] = {'posicao': int(posicao), 'pontos': int(pontos), 'ultimos_jogos': ultimos_jogos_str, 'jogos_disputados': jogos_disputados}
        print(f"✅ Dados de classificação para {len(estatisticas_times)} times processados com sucesso.")
        return estatisticas_times
    except Exception as e:
        print(f"   > Erro ao fazer web scraping da tabela de classificação: {e}")
        return {}

def buscar_stats_365scores():
    print("\nBuscando dados de estatísticas via Web Scraping do 365Scores (com Selenium)...")
    url = "https://www.365scores.com/pt-br/football/league/brasileirao-serie-a-113/stats"
    stats_365 = {}
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    service = ChromeService(ChromeDriverManager().install())
    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        print("   > Clicando na aba 'Times'...")
        times_button = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'secondary-tabs_tab_button') and text()='Times']")))
        driver.execute_script("arguments[0].click();", times_button)
        
        print("   > Aguardando 2 segundos para checar por popups...")
        time.sleep(2)
        try:
            print("   > Procurando por popup de propaganda para fechar...")
            close_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'external-ad_close_button')]")))
            driver.execute_script("arguments[0].click();", close_button)
            print("   > Popup fechado com sucesso.")
            time.sleep(1)
        except Exception:
            print(f"   > Nenhum popup encontrado. Continuando...")

        print("   > Aguardando tabelas carregarem...")
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//h2[text()='Gols por jogo']")))
        
        try:
            print("   > Procurando e clicando em TODOS os botões 'Ver mais'...")
            ver_mais_buttons = driver.find_elements(By.XPATH, "//div[contains(text(), 'Ver mais')]")
            for button in ver_mais_buttons:
                driver.execute_script("arguments[0].click();", button)
            print("   > Todas as listas expandidas. Aguardando expansão...")
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//*[text()='Grêmio']")))
        except:
            print("   > AVISO: Nenhum botão 'Ver mais' encontrado ou falha na expansão. Continuando...")

        soup = BeautifulSoup(driver.page_source, 'lxml')
        
        titulos = {"Escanteios por jogo": "media_escanteios", "Cartões Amarelos": "total_amarelos", "Cartões Vermelhos": "total_vermelhos"}
        for titulo_texto, stat_key in titulos.items():
            titulo_tag = soup.find('h2', string=titulo_texto)
            if not titulo_tag:
                print(f"   > AVISO: Tabela '{titulo_texto}' não encontrada.")
                continue

            container_geral = titulo_tag.find_parent('div', class_=lambda c: c and c.startswith('entity-stats-widget_content'))
            if not container_geral:
                print(f"   > AVISO: Container geral para '{titulo_texto}' não encontrado.")
                continue

            linhas = container_geral.find_all('a', class_=lambda c: c and c.startswith('entity-stats-widget_row'))
            for linha in linhas:
                nome_tag = linha.find('span', class_=lambda c: c and c.startswith('entity-stats-widget_player_name'))
                valor_tag = linha.find('div', class_=lambda c: c and c.startswith('entity-stats-widget_stats_value'))
                if nome_tag and valor_tag:
                    nome_time = nome_tag.text.strip()
                    if nome_time not in stats_365:
                        stats_365[nome_time] = {}
                    try:
                        valor = float(valor_tag.text.strip())
                        stats_365[nome_time][stat_key] = valor
                    except ValueError:
                        continue
        
        print(f"✅ Dados de estatísticas para {len(stats_365)} times coletados com sucesso do 365Scores.")
        return stats_365
        
    except Exception as e:
        print(f"   > Erro ao fazer web scraping do 365Scores com Selenium: {e}")
        return {}
    finally:
        if driver:
            driver.quit()

# --- FUNÇÃO PRINCIPAL DE EXECUÇÃO ---
def main_run():
    """Executa um ciclo completo de coleta, validação e salvamento dos dados."""
    print(f"\n{'='*20} INICIANDO CICLO DE COLETA - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} {'='*20}")
    
    limpar_tabelas()
    
    dados_jogadores, dados_times_cbf, jogos_finalizados, todas_as_partidas = buscar_dados_campeonato_completo(ID_COMPETICAO_CBF, TOTAL_RODADAS)
    
    if len(dados_times_cbf) < 20:
        print(f"❌ ERRO DE VALIDAÇÃO: A API da CBF retornou apenas {len(dados_times_cbf)} times. Abortando ciclo.")
        sys.exit(1)

    estatisticas_dos_times = buscar_classificacao_com_scraping(ANO_COMPETICAO, dados_times_cbf)
    
    if len(estatisticas_dos_times) < 20:
        print(f"❌ ERRO DE VALIDAÇÃO: O scraping da CBF retornou apenas {len(estatisticas_dos_times)} times. Abortando ciclo.")
        sys.exit(1)
    
    stats_365 = buscar_stats_365scores()

    if len(stats_365) < 20:
        print(f"❌ ERRO DE VALIDAÇÃO: O scraping do 365Scores retornou apenas {len(stats_365)} times. Abortando ciclo.")
        sys.exit(1)

    # Combina os dados de estatísticas
    nome_para_id_cbf = {info['nome']: time_id for time_id, info in dados_times_cbf.items()}
    for nome_365, stats in stats_365.items():
        nome_cbf = MAPA_NOMES_EXTERNOS_PARA_CBF.get(nome_365, nome_365)
        time_id = nome_para_id_cbf.get(nome_cbf)
        
        if time_id and time_id in estatisticas_dos_times:
            jogos_disputados = estatisticas_dos_times[time_id].get('jogos_disputados', 0)
            
            total_amarelos = stats.get('total_amarelos', 0)
            if jogos_disputados > 0:
                media = float(total_amarelos) / jogos_disputados
                estatisticas_dos_times[time_id]['media_amarelos'] = round(media, 2)
            else:
                estatisticas_dos_times[time_id]['media_amarelos'] = 0
            
            estatisticas_dos_times[time_id]['total_vermelhos'] = stats.get('total_vermelhos', 0)
            estatisticas_dos_times[time_id]['media_escanteios'] = stats.get('media_escanteios', 0)
        else:
            print(f"   > AVISO DE MAPEAMENTO: Não foi possível encontrar o time '{nome_365}' (traduzido para '{nome_cbf}') no dicionário da CBF.")

    salvar_dados_no_banco(dados_jogadores, dados_times_cbf, jogos_finalizados, todas_as_partidas, estatisticas_dos_times)
    print(f"\n✅ CICLO CONCLUÍDO COM SUCESSO.")

# --- FLUXO PRINCIPAL (SIMPLIFICADO PARA O SERVIDOR) ---
if __name__ == "__main__":
    criar_banco_de_dados()
    main_run()