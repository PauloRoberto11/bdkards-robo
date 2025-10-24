import requests
from bs4 import BeautifulSoup
import json
import time
import sqlite3
import os
import sys
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURAÇÕES GLOBAIS ---
# O caminho agora aponta para a pasta 'database' dentro do seu projeto Flutter no diretório pai
DB_FOLDER_PATH = os.path.join(os.getcwd(), '..', 'bdkards', 'database') 
DB_FILE = os.path.join(DB_FOLDER_PATH, 'brasileirao.db')
ID_COMPETICAO_CBF = 12606
ANO_COMPETICAO = 2025
TOTAL_RODADAS = 38
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

MAPA_NOMES_365_PARA_CBF = {
    "Atlético-MG": "Atlético Mineiro Saf", "RB Bragantino": "Red Bull Bragantino",
    "São Paulo": "São Paulo", "Flamengo": "Flamengo", "Corinthians": "Corinthians",
    "Vasco da Gama": "Vasco da Gama S.a.f.", "Vasco": "Vasco da Gama S.a.f.",
    "Bahia": "Bahia", "Vitória": "Vitória", "Fortaleza": "Fortaleza Ec Saf",
    "Ceará": "Ceará", "Mirassol": "Mirassol", "Sport Recife": "Sport", "Juventude": "Juventude",
    "Grêmio": "Grêmio", "Palmeiras": "Palmeiras", "Fluminense": "Fluminense",
    "Santos": "Santos Fc", "Botafogo": "Botafogo", "Internacional": "Internacional",
    "Cruzeiro": "Cruzeiro Saf",
    "Athletico-PR": "Athletico Paranaense", "Atlético-GO": "Atlético Goianiense Saf",
    "Criciúma": "Criciúma", "Cuiabá": "Cuiabá Saf"
}

# --- FUNÇÕES DO BANCO DE DADOS ---
def criar_banco_de_dados():
    os.makedirs(DB_FOLDER_PATH, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS times (id INTEGER PRIMARY KEY, nome TEXT NOT NULL UNIQUE, url_escudo TEXT)')
    cursor.execute('''CREATE TABLE IF NOT EXISTS atletas (id INTEGER PRIMARY KEY, apelido TEXT NOT NULL, cartoes_amarelos INTEGER DEFAULT 0, cartoes_vermelhos INTEGER DEFAULT 0, rodada_ultimo_vermelho INTEGER DEFAULT 0, rodada_suspensao_amarelo INTEGER DEFAULT 0, time_id INTEGER, FOREIGN KEY (time_id) REFERENCES times (id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS jogos_finalizados (id_jogo INTEGER PRIMARY KEY, rodada INTEGER NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS partidas (
        id_jogo INTEGER PRIMARY KEY, rodada INTEGER NOT NULL, data TEXT, hora TEXT, local TEXT,
        mandante_nome TEXT, mandante_url_escudo TEXT, mandante_gols TEXT, mandante_formacao TEXT,
        visitante_nome TEXT, visitante_url_escudo TEXT, visitante_gols TEXT, visitante_formacao TEXT
    )''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estatisticas_time (
            time_id INTEGER PRIMARY KEY, posicao INTEGER, pontos INTEGER, ultimos_jogos TEXT,
            media_cartoes_amarelos REAL, total_cartoes_vermelhos INTEGER, media_escanteios REAL,
            FOREIGN KEY (time_id) REFERENCES times (id)
        )''')
    # DROP para garantir que a nova estrutura com colunas de imagem e posição seja criada
    cursor.execute('DROP TABLE IF EXISTS escalacoes')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS escalacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jogo_id INTEGER,
            time_nome TEXT,
            nome_jogador TEXT,
            numero_camisa TEXT,
            posicao TEXT,
            is_titular INTEGER,
            foto_url TEXT,
            pos_x REAL,
            pos_y REAL,
            FOREIGN KEY (jogo_id) REFERENCES partidas (id_jogo)
        )''')
    conn.commit()
    conn.close()
    print(f"Banco de dados verificado/criado em: {DB_FILE}")

def limpar_tabelas():
    # Esta função se torna redundante, pois criar_banco_de_dados já limpa a tabela principal,
    # mas a mantemos para clareza do fluxo.
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    print("Recriando tabelas (DROP/CREATE)...")
    cursor.execute("DROP TABLE IF EXISTS escalacoes")
    cursor.execute("DROP TABLE IF EXISTS atletas")
    cursor.execute("DROP TABLE IF EXISTS times")
    cursor.execute("DROP TABLE IF EXISTS jogos_finalizados")
    cursor.execute("DROP TABLE IF EXISTS partidas")
    cursor.execute("DROP TABLE IF EXISTS estatisticas_time")
    conn.commit()
    conn.close()
    print("Tabelas antigas removidas.")

def salvar_dados_no_banco(estatisticas_jogadores, times_info, jogos_finalizados_info, todas_as_partidas_info, estatisticas_times, todas_as_escalacoes):
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
        cursor.execute('''INSERT OR REPLACE INTO partidas (
            id_jogo, rodada, data, hora, local, mandante_nome, mandante_url_escudo, mandante_gols, mandante_formacao, 
            visitante_nome, visitante_url_escudo, visitante_gols, visitante_formacao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (jogo['id_jogo'], jogo['rodada'], jogo['data'], jogo['hora'], jogo['local'],
            jogo['mandante_nome'], jogo['mandante_url_escudo'], jogo['mandante_gols'], jogo.get('mandante_formacao'),
            jogo['visitante_nome'], jogo['visitante_url_escudo'], jogo['visitante_gols'], jogo.get('visitante_formacao')))

    if todas_as_escalacoes:
        print("Salvando escalações...")
        for jogo_id, escalacao_jogo in todas_as_escalacoes.items():
            if not escalacao_jogo: continue

            if 'mandante' in escalacao_jogo:
                time_mandante = escalacao_jogo['mandante']
                for jogador in time_mandante.get('titulares', []):
                    cursor.execute('INSERT INTO escalacoes (jogo_id, time_nome, nome_jogador, numero_camisa, is_titular, foto_url, pos_x, pos_y) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                                   (jogo_id, time_mandante['nome'], jogador['nome'], jogador['numero'], 1, jogador.get('foto_url'), jogador.get('pos_x'), jogador.get('pos_y')))
                for jogador in time_mandante.get('reservas', []):
                    cursor.execute('INSERT INTO escalacoes (jogo_id, time_nome, nome_jogador, numero_camisa, is_titular, posicao) VALUES (?, ?, ?, ?, ?, ?)',
                                   (jogo_id, time_mandante['nome'], jogador['nome'], jogador['numero'], 0, jogador['posicao']))
                for jogador in time_mandante.get('fora_de_jogo', []):
                    cursor.execute('INSERT INTO escalacoes (jogo_id, time_nome, nome_jogador, is_titular, posicao) VALUES (?, ?, ?, ?, ?)',
                                   (jogo_id, time_mandante['nome'], jogador['nome'], 0, f"Ausente ({jogador['motivo']})"))

            if 'visitante' in escalacao_jogo:
                time_visitante = escalacao_jogo['visitante']
                for jogador in time_visitante.get('titulares', []):
                    cursor.execute('INSERT INTO escalacoes (jogo_id, time_nome, nome_jogador, numero_camisa, is_titular, foto_url, pos_x, pos_y) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                                   (jogo_id, time_visitante['nome'], jogador['nome'], jogador['numero'], 1, jogador.get('foto_url'), jogador.get('pos_x'), jogador.get('pos_y')))
                for jogador in time_visitante.get('reservas', []):
                    cursor.execute('INSERT INTO escalacoes (jogo_id, time_nome, nome_jogador, numero_camisa, is_titular, posicao) VALUES (?, ?, ?, ?, ?, ?)',
                                   (jogo_id, time_visitante['nome'], jogador['nome'], jogador['numero'], 0, jogador['posicao']))
                for jogador in time_visitante.get('fora_de_jogo', []):
                    cursor.execute('INSERT INTO escalacoes (jogo_id, time_nome, nome_jogador, is_titular, posicao) VALUES (?, ?, ?, ?, ?)',
                                   (jogo_id, time_visitante['nome'], jogador['nome'], 0, f"Ausente ({jogador['motivo']})"))

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


# --- FUNÇÕES DE COLETA DO 365SCORES (ISOLADAS) ---
def handle_cookie_banner(driver):
    try:
        wait = WebDriverWait(driver, 5)
        agree_button = wait.until(EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button")))
        driver.execute_script("arguments[0].click();", agree_button)
        print("   > Banner de cookie aceito.")
        time.sleep(2)
    except Exception:
        pass

def handle_ad_popup(driver):
    try:
        wait = WebDriverWait(driver, 3)
        close_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'external-ad_close_button')]")))
        driver.execute_script("arguments[0].click();", close_button)
        print("   > Popup de propaganda fechado.")
        time.sleep(1)
    except Exception:
        pass

def extrair_dados_time(widget_content):
    dados = {'titulares': [], 'reservas': [], 'fora_de_jogo': [], 'formacao': ''}
    try:
        dados['formacao'] = widget_content.find('bdi', class_=lambda c: c and 'lineups-widget_status_text' in c).text.strip()
    except AttributeError:
        print("     - Aviso: Formação não encontrada.")
        
    canvas_container = widget_content.find('div', class_=lambda c: c and 'field-formation_canvas_relative_container' in c)
    if canvas_container:
        container_style = canvas_container.get('style', '')
        width_match = re.search(r'width:\s*([\d.]+)px', container_style)
        height_match = re.search(r'height:\s*([\d.]+)px', container_style)
        
        container_width = float(width_match.group(1)) if width_match and width_match.group(1) else 1.0
        container_height = float(height_match.group(1)) if height_match and height_match.group(1) else 1.0
        
        if container_width == 0: container_width = 1.0
        if container_height == 0: container_height = 1.0

        titulares_tags = canvas_container.find_all('a', class_=lambda c: c and 'field-formation_player_container' in c)
        for j_tag in titulares_tags:
            style = j_tag.get('style', '')
            left_match = re.search(r'left:\s*([\d.-]+)px', style)
            bottom_match = re.search(r'bottom:\s*([\d.-]+)px', style)
            
            pos_x_px = float(left_match.group(1)) if left_match else 0.0
            pos_y_px = float(bottom_match.group(1)) if bottom_match else 0.0

            dados['titulares'].append({
                'nome': j_tag.find('div', class_=lambda c: c and 'field-formation_player_name' in c).text.strip(),
                'numero': j_tag.find('div', class_=lambda c: c and 'field-formation_player_number_text' in c).text.strip(),
                'foto_url': j_tag.find('img').get('src', ''),
                'pos_x': (pos_x_px / container_width) * 100,
                'pos_y': (pos_y_px / container_height) * 100,
            })
    print(f"     - {len(dados['titulares'])} titulares encontrados.")

    listas_jogadores = widget_content.find_all('div', class_=lambda c: c and 'players-list-container' in c)
    for lista in listas_jogadores:
        titulo_tag = lista.find(['h2', 'h3'], class_=lambda c: c and 'card-title_title' in c)
        if not titulo_tag: continue

        if 'Banco' in titulo_tag.text:
            reservas = lista.find_all('a', class_=lambda c: c and 'players-list-item' in c)
            for j in reservas:
                num_div = j.find('div', class_=lambda c: c and 'players-list-item-player-number' in c)
                pos_tag = j.find('div', class_=lambda c: c and 'players-list-item-player-position' in c)
                dados['reservas'].append({
                    'nome': j.find('div', class_=lambda c: c and 'players-list-item-player-name' in c).text.strip(),
                    'numero': num_div.div.text.strip() if num_div and num_div.div else 'S/N',
                    'posicao': pos_tag.text.strip() if pos_tag else 'N/A'
                })
            print(f"     - {len(dados['reservas'])} reservas encontrados.")
        elif 'Fora do jogo' in titulo_tag.text:
            ausentes = lista.find_all('a', class_=lambda c: c and 'players-list-item' in c)
            for j in ausentes:
                motivo = 'Indisponível'
                if j.find('div', class_=lambda c: c and 'suspension' in c): motivo = 'Suspenso'
                elif j.find('div', class_=lambda c: c and 'injuries' in c): motivo = 'Lesionado'
                pos_tag = j.find('div', class_=lambda c: c and 'players-list-item-player-position' in c)
                dados['fora_de_jogo'].append({
                    'nome': j.find('div', class_=lambda c: c and 'players-list-item-player-name' in c).text.strip(),
                    'posicao': pos_tag.text.strip() if pos_tag else 'N/A',
                    'motivo': motivo
                })
            print(f"     - {len(dados['fora_de_jogo'])} jogadores fora de jogo encontrados.")
    return dados

def buscar_stats_365scores():
    print("\nBuscando dados de estatísticas via Web Scraping do 365Scores...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1280')
    service = ChromeService(ChromeDriverManager().install())
    driver = None
    stats_365 = {}
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://www.365scores.com/pt-br/football/league/brasileirao-serie-a-113/stats")
        handle_cookie_banner(driver)

        print("   > Clicando na aba 'Times'...")
        times_button = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'secondary-tabs_tab_button') and text()='Times']")))
        driver.execute_script("arguments[0].click();", times_button)
        
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
        
        print(f"✅ Dados de estatísticas para {len(stats_365)} times coletados com sucesso.")
        return stats_365
        
    except Exception as e:
        print(f"   > ❌ Erro ao fazer web scraping de estatísticas: {e}")
        return {}
    finally:
        if driver:
            driver.quit()
            print("   > Navegador de estatísticas fechado.")


def buscar_escalacoes_da_rodada(proxima_rodada, jogos_da_proxima_rodada_cbf, mapa_nomes_cbf_para_365):
    print(f"\nBuscando escalações para a rodada {proxima_rodada} no 365Scores...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    service = ChromeService(ChromeDriverManager().install())
    driver = None
    todas_as_escalacoes = {}

    try:
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 20)
        
        url_fixtures = "https://www.365scores.com/pt-br/football/league/brasileirao-serie-a-113/matches#fixtures"
        driver.get(url_fixtures)
        handle_cookie_banner(driver)
        
        print("   > Desenrolando o papiro de jogos para carregar todas as rodadas...")
        last_height = 0
        max_scrolls = 15 
        for i in range(max_scrolls):
            driver.execute_script("window.scrollBy(0, window.innerHeight);")
            time.sleep(2)

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print(f"   > Fim da página alcançado na rolagem #{i+1}. Todos os jogos devem estar carregados.")
                break
            last_height = new_height
        
        xpath_rodada_365 = f"//div[contains(@class, 'entity-scores-widget-group_header_title') and text()='Rodada {proxima_rodada}']"
        rodada_elements_365 = wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath_rodada_365)))
        
        mapa_jogo_para_url = {}
        for rodada_element in rodada_elements_365:
            container_pai_rodada = rodada_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'entity-scores-widget-group_container')]")
            links_jogos_365 = container_pai_rodada.find_elements(By.XPATH, ".//a[contains(@class, 'game-card_game_card_link__L3moj')]")
            for link in links_jogos_365:
                nomes = link.find_elements(By.XPATH, ".//div[contains(@class, 'game-card-competitor_name')]")
                if len(nomes) == 2:
                    mandante = nomes[0].text.strip(); visitante = nomes[1].text.strip()
                    chave_jogo = f"{mandante}-{visitante}"
                    mapa_jogo_para_url[chave_jogo] = link.get_attribute('href')
        
        print(f"   > {len(mapa_jogo_para_url)} URLs de jogos mapeadas para a rodada {proxima_rodada}.")

        for i, jogo_cbf in enumerate(jogos_da_proxima_rodada_cbf):
            print(f"\n--- Processando Jogo {i+1}/{len(jogos_da_proxima_rodada_cbf)} da Rodada {proxima_rodada} ---")
            
            nome_mandante_365 = mapa_nomes_cbf_para_365.get(jogo_cbf['mandante_nome'])
            nome_visitante_365 = mapa_nomes_cbf_para_365.get(jogo_cbf['visitante_nome'])

            if not (nome_mandante_365 and nome_visitante_365):
                print(f"   > AVISO: Nomes não mapeados para: {jogo_cbf['mandante_nome']} vs {jogo_cbf['visitante_nome']}. Pulando.")
                continue
            
            chave_jogo_atual = f"{nome_mandante_365}-{nome_visitante_365}"
            url_jogo_365 = mapa_jogo_para_url.get(chave_jogo_atual)

            if not url_jogo_365:
                print(f"   > AVISO: URL não encontrada para o jogo {chave_jogo_atual}. Pulando.")
                continue

            print(f"   > URL do jogo: {url_jogo_365}")
            
            try:
                driver.get(url_jogo_365)
                handle_cookie_banner(driver)
                handle_ad_popup(driver)

                print("     - Clicando em 'Escalação provável'...")
                escalacao_tab = wait.until(EC.element_to_be_clickable((By.ID, "navigation-tabs_game-center_lineups")))
                driver.execute_script("arguments[0].click();", escalacao_tab)
                
                xpath_campo_futebol = "//div[contains(@class, 'game-center-widget_content')]//div[contains(@class, 'field-formation_field_container')]"
                wait.until(EC.presence_of_element_located((By.XPATH, xpath_campo_futebol)))
                time.sleep(1)

                jogo_atual = {}

                print(f"     - Extraindo dados de: {nome_mandante_365} (Mandante)")
                soup_mandante = BeautifulSoup(driver.page_source, 'lxml')
                widget_content_mandante = soup_mandante.find('div', class_=lambda c: c and 'game-center-widget_content' in c)
                if widget_content_mandante:
                    jogo_atual['mandante'] = {'nome': jogo_cbf['mandante_nome'], **extrair_dados_time(widget_content_mandante)}

                botoes_time = driver.find_elements(By.XPATH, "//div[contains(@class, 'secondary-tabs_tab_button_container')]")
                if len(botoes_time) > 1:
                    driver.execute_script("arguments[0].click();", botoes_time[1])
                    time.sleep(3)
                    
                    print(f"     - Extraindo dados de: {nome_visitante_365} (Visitante)")
                    soup_visitante = BeautifulSoup(driver.page_source, 'lxml')
                    widget_content_visitante = soup_visitante.find('div', class_=lambda c: c and 'game-center-widget_content' in c)
                    if widget_content_visitante:
                        jogo_atual['visitante'] = {'nome': jogo_cbf['visitante_nome'], **extrair_dados_time(widget_content_visitante)}
                
                todas_as_escalacoes[jogo_cbf['id_jogo']] = jogo_atual

            except Exception:
                print("   > Por enquanto, não temos nenhuma escalação disponível para esse jogo.")
                print(f"     - (Jogo: {nome_mandante_365} vs {nome_visitante_365})")
                continue

        return todas_as_escalacoes

    except Exception as e:
        print(f"   > ❌ Erro ao buscar escalações da rodada: {e}")
        return todas_as_escalacoes
    finally:
        if driver:
            driver.quit()
            print("   > Navegador de escalações fechado.")

def main_run():
    print(f"\n{'='*20} INICIANDO CICLO DE COLETA - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} {'='*20}")
    
    limpar_tabelas()
    criar_banco_de_dados()
    
    dados_jogadores, dados_times_cbf, jogos_finalizados, todas_as_partidas = buscar_dados_campeonato_completo(ID_COMPETICAO_CBF, TOTAL_RODADAS)
    
    if len(dados_times_cbf) < 20: sys.exit(f"❌ ERRO: API da CBF retornou apenas {len(dados_times_cbf)} times.")

    estatisticas_dos_times = buscar_classificacao_com_scraping(ANO_COMPETICAO, dados_times_cbf)
    
    if len(estatisticas_dos_times) < 20: sys.exit(f"❌ ERRO: Scraping da CBF retornou apenas {len(estatisticas_dos_times)} times.")
    
    stats_365 = buscar_stats_365scores()
    if stats_365 and len(stats_365) < 20: 
        print(f"⚠️ AVISO: Scraping de estatísticas retornou apenas {len(stats_365)} times. Continuando mesmo assim.")

    rodada_atual = max([jogo['rodada'] for jogo in jogos_finalizados]) if jogos_finalizados else 0
    proxima_rodada = rodada_atual + 1
    
    if proxima_rodada > TOTAL_RODADAS:
        print("Campeonato finalizado. Nenhuma nova escalação para buscar.")
    else:
        jogos_da_proxima_rodada_cbf = [jogo for jogo in todas_as_partidas if jogo['rodada'] == proxima_rodada]
        mapa_nomes_cbf_para_365 = {v: k for k, v in MAPA_NOMES_365_PARA_CBF.items()}
        todas_as_escalacoes = buscar_escalacoes_da_rodada(proxima_rodada, jogos_da_proxima_rodada_cbf, mapa_nomes_cbf_para_365)
        
        for jogo_id, escalacao_data in todas_as_escalacoes.items():
            for i, partida in enumerate(todas_as_partidas):
                if partida['id_jogo'] == jogo_id:
                    if 'mandante' in escalacao_data and 'formacao' in escalacao_data['mandante']:
                        todas_as_partidas[i]['mandante_formacao'] = escalacao_data['mandante']['formacao']
                    if 'visitante' in escalacao_data and 'formacao' in escalacao_data['visitante']:
                        todas_as_partidas[i]['visitante_formacao'] = escalacao_data['visitante']['formacao']
                    break

    if estatisticas_dos_times and stats_365:
        nome_para_id_cbf = {info['nome']: time_id for time_id, info in dados_times_cbf.items()}
        for nome_365, stats in stats_365.items():
            nome_cbf = MAPA_NOMES_365_PARA_CBF.get(nome_365, nome_365)
            time_id = nome_para_id_cbf.get(nome_cbf)
            
            if time_id and time_id in estatisticas_dos_times:
                jogos_disputados = estatisticas_dos_times[time_id].get('jogos_disputados', 0)
                total_amarelos = stats.get('total_amarelos', 0)
                estatisticas_dos_times[time_id]['media_amarelos'] = round(float(total_amarelos) / jogos_disputados, 2) if jogos_disputados > 0 else 0
                estatisticas_dos_times[time_id]['total_vermelhos'] = stats.get('total_vermelhos', 0)
                estatisticas_dos_times[time_id]['media_escanteios'] = stats.get('media_escanteios', 0)
            else:
                print(f"   > AVISO DE MAPEAMENTO: Não foi possível encontrar o time '{nome_365}' (traduzido para '{nome_cbf}') no dicionário da CBF.")

    salvar_dados_no_banco(dados_jogadores, dados_times_cbf, jogos_finalizados, todas_as_partidas, estatisticas_dos_times, todas_as_escalacoes if 'todas_as_escalacoes' in locals() else {})
    print(f"\n✅ CICLO CONCLUÍDO COM SUCESSO.")

if __name__ == "__main__":
    main_run()