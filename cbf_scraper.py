import os
import sys
import re
import time
import sqlite3
from typing import Optional
from datetime import datetime
from unidecode import unidecode

# Bibliotecas para Web Scraping
import requests
from bs4 import BeautifulSoup

# Bibliotecas para Web Scraping Dinâmico (Selenium)
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==============================================================================
# VARIÁVEIS GLOBAIS E CONSTANTES (A SEREM PREENCHIDAS)
# ==============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER_PATH = os.path.join(SCRIPT_DIR, 'database')
DB_FILE = os.path.join(DB_FOLDER_PATH, 'brasileirao.db')

if not os.path.exists(DB_FOLDER_PATH):
    os.makedirs(DB_FOLDER_PATH, exist_ok=True)
    print(f"📁 Pasta do banco de dados criada em: {DB_FOLDER_PATH}")

# Constantes da Competição
ID_COMPETICAO_CBF = 12606  # Substituir pelo ID real da competição na API da CBF
ANO_COMPETICAO = 2025
TOTAL_RODADAS = 38

# Headers para requisições HTTP
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# MAPAS DE NORMALIZAÇÃO CRÍTICOS (Exemplos)
# Usado para mapear o nome longo da API CBF para o nome curto no site CBF (para o scraping)
MAPA_NOMES_365_PARA_CBF = {
    
    "Atlético-MG": "Atlético Mineiro Saf", 
    "Bahia": "Bahia",
    "Botafogo": "Botafogo", 
    "Ceará": "Ceará",
    "Corinthians": "Corinthians",
    "Cruzeiro": "Cruzeiro Saf",
    "Flamengo": "Flamengo",
    "Fluminense": "Fluminense",
    "Fortaleza": "Fortaleza Ec Saf",
    "Grêmio": "Grêmio",
    "Internacional": "Internacional",
    "Juventude": "Juventude",
    "Mirassol": "Mirassol",
    "Palmeiras": "Palmeiras",
    "RB Bragantino": "Red Bull Bragantino",
    "Santos": "Santos Fc",
    "São Paulo": "São Paulo",  
    "Sport": "Sport Recife",
    "Sport Recife": "Sport Recife", # NOVO: Chave exata que o scraping está encontrando
    "Vasco": "Vasco da Gama S.a.f.",
    "Vitória": "Vitória", 
      
}

# --- MAPA DE NORMALIZAÇÃO CBF API (LONGO) -> CBF SITE (CURTO) ---
# Usado para forçar a correspondência de nomes problemáticos (SAF, Sport, etc.)
MAPA_NORMALIZACAO_NOME_CBF_SITE = {
    "Atlético Mineiro Saf": "Atlético-MG",
    "Bahia": "Bahia",
    "Botafogo": "Botafogo", 
    "Ceará": "Ceará",
    "Corinthians": "Corinthians",
    "Cruzeiro Saf": "Cruzeiro",
    "Flamengo": "Flamengo",
    "Fluminense": "Fluminense",
    "Fortaleza Ec Saf": "Fortaleza",
    "Grêmio": "Grêmio",
    "Internacional": "Internacional",
    "Juventude": "Juventude",
    "Mirassol": "Mirassol",
    "Palmeiras": "Palmeiras",
    "Red Bull Bragantino": "RB Bragantino",
    "Santos Fc": "Santos",
    "São Paulo": "São Paulo",  
    "Sport Recife": "Sport Recife", 
    "Vasco da Gama S.a.f.": "Vasco da Gama",
    "Vitória": "Vitória", 
}

MAPA_ABREVIACOES = {
    "Atlético-MG":"Atlético-MG",
    "Bahia": "Bahia",
    "Botafogo": "Botafogo", 
    "Ceará": "Ceará",
    "Corinthians": "Corinthians",
    "Cruzeiro Saf": "Cruzeiro",
    "Flamengo": "Flamengo",
    "Fluminense": "Fluminense",
    "Fortaleza": "Fortaleza",
    "Grêmio": "Grêmio",
    "Internacional": "Inter-RS",
    "Juventude": "Juventude",
    "Mirassol": "Mirassol",
    "Palmeiras": "Palmeiras",
    "RB Bragantino": "Bragantino",
    "Santos Fc": "Santos",
    "São Paulo": "São Paulo",  
    "Sport": "Sport-PE", 
    "Vasco da Gama": "Vasco",
    "Vitória": "Vitória", 
}


URLS_ELENCO_365 = {
     "Atlético-MG": "https://www.365scores.com/pt-br/football/team/atletico-mineiro-1209/squad",
     "Bahia": "https://www.365scores.com/pt-br/football/team/bahia-1767/squad",
     "Botafogo": "https://www.365scores.com/pt-br/football/team/botafogo-1211/squad",
     "Ceara": "https://www.365scores.com/pt-br/football/team/ceara-1781/squad",
     "Corinthians": "https://www.365scores.com/pt-br/football/team/corinthians-1267/squad",
     "Cruzeiro": "https://www.365scores.com/pt-br/football/team/cruzeiro-1213/squad",
     "Flamengo": "https://www.365scores.com/pt-br/football/team/flamengo-1215/squad",
     "Fluminense": "https://www.365scores.com/pt-br/football/team/fluminense-1216/squad",
     "Fortaleza": "https://www.365scores.com/pt-br/football/team/fortaleza-1778/squad",
     "Grêmio": "https://www.365scores.com/pt-br/football/team/gremio-1218/squad",
     "Internacional": "https://www.365scores.com/pt-br/football/team/sc-internacional-1219/squad",
     "Juventude": "https://www.365scores.com/pt-br/football/team/juventude-1775/squad",
     "Mirassol": "https://www.365scores.com/pt-br/football/team/mirassol-1269/squad",
     "Palmeiras": "https://www.365scores.com/pt-br/football/team/palmeiras-1222/squad",
     "RB Bragantino": "https://www.365scores.com/pt-br/football/team/red-bull-bragantino-1273/squad",
     "Santos": "https://www.365scores.com/pt-br/football/team/santos-1224/squad",
     "São Paulo": "https://www.365scores.com/pt-br/football/team/sao-paulo-1225/squad",
     "Sport Recife": "https://www.365scores.com/pt-br/football/team/sport-recife-1226/squad",
     "Vasco": "https://www.365scores.com/pt-br/football/team/vasco-da-gama-1227/squad",
     "Vitória": "https://www.365scores.com/pt-br/football/team/vitoria-1228/squad"
 }

# ==============================================================================
# FUNÇÕES PLACEHOLDER (Assumidas das Partes não enviadas)
# ==============================================================================

def calcular_rodada_atual(jogos_finalizados, todas_as_partidas, TOTAL_RODADAS):
    """
    Calcula a rodada atual do campeonato com base nos jogos finalizados.
    A rodada atual é a próxima a ser jogada após a última rodada finalizada.
    """
    
    # 1. Encontra a última rodada completamente finalizada
    if jogos_finalizados:
        rodada_ultima_finalizada = max([jogo['rodada'] for jogo in jogos_finalizados])
    else:
        # Se nenhum jogo finalizado, a rodada inicial é 1
        return 1
    
    # Se já chegamos ao final do campeonato
    if rodada_ultima_finalizada >= TOTAL_RODADAS:
        print("⚠️ Campeonato finalizado. Usando a última rodada finalizada.")
        return TOTAL_RODADAS
    
    proxima_rodada = rodada_ultima_finalizada + 1

    # 2. Verificação de partidas restantes na rodada_ultima_finalizada:
    # Verifica se a rodada finalizada contém todos os seus jogos na lista de finalizados.
    # Se houver jogos da rodada_ultima_finalizada que AINDA NÃO estão em jogos_finalizados,
    # significa que a rodada ainda não terminou, então a rodada ATUAL é a última finalizada.
    
    # Cria um conjunto de IDs de jogos finalizados para lookup rápido
    ids_finalizados = {jogo['id_jogo'] for jogo in jogos_finalizados}
    
    # Encontra todos os jogos da rodada que é supostamente a última finalizada
    jogos_na_ultima_finalizada = [jogo for jogo in todas_as_partidas if jogo['rodada'] == rodada_ultima_finalizada]

    # Verifica se todos os jogos dessa rodada foram de fato finalizados
    if len(jogos_na_ultima_finalizada) != len([jogo for jogo in jogos_na_ultima_finalizada if jogo['id_jogo'] in ids_finalizados]):
        # Se os totais não baterem, há jogos faltando, a rodada AINDA NÃO ACABOU.
        return rodada_ultima_finalizada

    # Se a última rodada finalizada realmente terminou, a próxima rodada é a atual.
    return proxima_rodada

def ler_ultima_rodada_salva() -> int:
    """
    Lê a última rodada de escalações que foi salva com sucesso no banco de dados.
    
    Retorna:
        int: O número da última rodada processada. Retorna 0 se não for encontrado.
    """
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Cria a tabela de status se ela não existir
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS status_coleta (
                chave TEXT PRIMARY KEY,
                valor INTEGER
            );
        """)
        conn.commit()
        
        # Tenta ler o valor
        cursor.execute("SELECT valor FROM status_coleta WHERE chave = 'ultima_rodada_processada'")
        resultado = cursor.fetchone()
        
        if resultado:
            return int(resultado[0])
        else:
            return 0  # Retorna 0 se nunca foi salvo
            
    except sqlite3.Error as e:
        print(f"❌ Erro ao ler a última rodada salva: {e}")
        return 0
    finally:
        if conn:
            conn.close()

def salvar_ultima_rodada_processada(rodada: int):
    """
    Salva o número da rodada processada no banco de dados.
    
    Args:
        rodada (int): O número da rodada que foi salva com sucesso.
    """
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Usa INSERT OR REPLACE para garantir que sempre haja apenas uma entrada
        cursor.execute("""
            INSERT OR REPLACE INTO status_coleta (chave, valor) 
            VALUES (?, ?);
        """, ('ultima_rodada_processada', rodada))
        
        conn.commit()
        print(f"✅ Status: Rodada **{rodada}** salva com sucesso como a última rodada processada.")
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao salvar a última rodada processada: {e}")
    finally:
        if conn:
            conn.close()
def criar_banco_de_dados():
    # Supondo que DB_FOLDER_PATH e DB_FILE estejam definidos no escopo global/do módulo
    # Se não estiverem, você precisará defini-los ou passá-los como argumentos.
    try:
        # Tenta simular a definição se as variáveis não existirem (apenas para este bloco)
        DB_FOLDER_PATH = "database" 
        DB_FILE = os.path.join(DB_FOLDER_PATH, "brasileirao.db")
    except NameError:
        pass # Ignora se já estiverem definidas
    
    os.makedirs(DB_FOLDER_PATH, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. DROP NAS TABELAS ANTIGAS/REMOVIDAS (Para limpar a estrutura anterior)
    cursor.execute("DROP TABLE IF EXISTS escalacoes")
    cursor.execute("DROP TABLE IF EXISTS atletas")
    
    # DROP NAS TABELAS EXISTENTES (Para garantir que o schema é o novo)
    cursor.execute("DROP TABLE IF EXISTS elenco")
    cursor.execute("DROP TABLE IF EXISTS partidas_elenco")
    cursor.execute("DROP TABLE IF EXISTS times")
    cursor.execute("DROP TABLE IF EXISTS jogos_finalizados")
    cursor.execute("DROP TABLE IF EXISTS partidas")
    cursor.execute("DROP TABLE IF EXISTS estatisticas_time")
    
    # 2. CRIAÇÃO DAS TABELAS BASE
    
    # Tabela TIMES (id é o ID CBF)
    cursor.execute('CREATE TABLE IF NOT EXISTS times (id INTEGER PRIMARY KEY, nome TEXT NOT NULL UNIQUE, url_escudo TEXT, nome_curto TEXT)')
    
    # Tabela ELENCO (Novo Cadastro Mestre de Jogadores)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS elenco (
            id_jogador INTEGER PRIMARY KEY, -- Novo ID único global do jogador
            id_time INTEGER NOT NULL,      -- ID do time (Chave estrangeira)
            nome_jogador TEXT NOT NULL,
            numero TEXT,
            posicao TEXT,                  -- Posição principal do jogador (Ex: ZAGUEIRO, MEIA, ATACANTE)
            url_foto TEXT,
            UNIQUE(id_time, nome_jogador), -- Garante unicidade do jogador DENTRO DO TIME
            FOREIGN KEY (id_time) REFERENCES times (id)
        )
    ''')
    
    # Tabela ATLETAS (Mantida para dados de Cartões/Suspensão da API CBF)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS atletas (
            id INTEGER PRIMARY KEY, 
            apelido TEXT NOT NULL, 
            cartoes_amarelos INTEGER DEFAULT 0, 
            cartoes_vermelhos INTEGER DEFAULT 0, 
            rodada_ultimo_vermelho INTEGER DEFAULT 0, 
            rodada_suspensao_amarelo INTEGER DEFAULT 0, 
            time_id INTEGER, 
            FOREIGN KEY (time_id) REFERENCES times (id)
        )
    ''')

    # Tabela JOGOS FINALIZADOS
    cursor.execute('''CREATE TABLE IF NOT EXISTS jogos_finalizados (id_jogo INTEGER PRIMARY KEY, rodada INTEGER NOT NULL)''')
    
    # Tabela PARTIDAS (ID de jogo é o ID CBF, referenciado por ID de time)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partidas (
            id_jogo INTEGER PRIMARY KEY, 
            rodada INTEGER NOT NULL, 
            data TEXT, hora TEXT, local TEXT,
            mandante_id INTEGER, 
            mandante_url_escudo TEXT, 
            mandante_gols TEXT, 
            mandante_formacao TEXT,
            visitante_id INTEGER, 
            visitante_url_escudo TEXT, 
            visitante_gols TEXT, 
            visitante_formacao TEXT,
            FOREIGN KEY (mandante_id) REFERENCES times (id),
            FOREIGN KEY (visitante_id) REFERENCES times (id)
        )
    ''')
    
    # Tabela ESTATISTICAS_TIME
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estatisticas_time (
            time_id INTEGER PRIMARY KEY, 
            posicao INTEGER, 
            pontos INTEGER, 
            ultimos_jogos TEXT,
            media_cartoes_amarelos REAL,
            total_cartoes_vermelhos INTEGER, 
            media_escanteios REAL,
            FOREIGN KEY (time_id)
            REFERENCES times (id)
        )
    ''')
    
    # Tabela de LIGAÇÃO PARTIDAS_ELENCO (Mapeia qual jogador jogou em qual jogo)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partidas_elenco (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jogo_id INTEGER NOT NULL,
            id_time INTEGER NOT NULL,              -- Para saber de qual time a escalação pertence
            id_jogador INTEGER NOT NULL,           -- Chave para o jogador no ELENCO
            papel TEXT NOT NULL,                   -- TITULAR, RESERVA, AUSENTE
            pos_x REAL,                            -- Posição X (apenas se titular)
            pos_y REAL,                            -- Posição Y (apenas se titular)
            motivo TEXT,                           -- Lesão/Suspensão (apenas se AUSENTE)
            UNIQUE(jogo_id, id_time, id_jogador),  -- Garante que o jogador só aparece uma vez por time/jogo
            FOREIGN KEY (jogo_id) REFERENCES partidas (id_jogo),
            FOREIGN KEY (id_time) REFERENCES times (id),
            FOREIGN KEY (id_jogador) REFERENCES elenco (id_jogador)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Banco de dados verificado/criado em: {DB_FILE}")
    print("✅ Nova tabela ELENCO e PARTIDAS_ELENCO criadas com sucesso para resolver o conflito de fotos.")

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
                    todas_as_partidas_info.append({'id_jogo': jogo_id, 'rodada': i, 'data': jogo.get('data'), 'hora': jogo.get('hora'), 'local': jogo.get('local'), 'mandante_id': mandante.get('id'), 'mandante_nome': mandante.get('nome'), 'mandante_url_escudo': mandante.get('url_escudo'), 'mandante_gols': mandante.get('gols'), 'visitante_id': visitante.get('id'), 'visitante_nome': visitante.get('nome'), 'visitante_url_escudo': visitante.get('url_escudo'), 'visitante_gols': visitante.get('gols')})
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

def salvar_dados_no_banco(estatisticas_jogadores, times_info, jogos_finalizados_info, todas_as_partidas_info, estatisticas_times, todas_as_escalacoes, lista_final_elenco):
    """
    Salva todos os dados coletados, utilizando a nova estrutura de banco de dados:
    - TIMES
    - ELENCO (Mestre de Jogadores com foto única por time)
    - ESTATISTICAS_TIME
    - PARTIDAS (Cabeçalho)
    - PARTIDAS_ELENCO (Ligação de Jogador/Jogo)
    - ATLETAS (Dados da CBF - Mantidos, mas não alterados aqui)
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
    except NameError:
        print("❌ ERRO FATAL: Variáveis de caminho do DB (DB_FILE/DB_FOLDER_PATH) não definidas. Não foi possível conectar ao banco.")
        return

    print("\nSalvando novos dados consolidados no banco de dados...")

    # --- 1. TIMES ---
    print(f"   > Salvando {len(times_info)} times...")
    for time_id, dados_time in times_info.items():
        # Nota: Usei 'nome_curto' e 'url_escudo' que foram populados na Parte I/II
        cursor.execute('INSERT OR REPLACE INTO times (id, nome, url_escudo, nome_curto) VALUES (?, ?, ?, ?)', 
                       (time_id, dados_time.get('nome'), dados_time.get('url_escudo'), dados_time.get('nome_curto')))

    # --- 2. ELENCO MESTRE (RESOLVE O PROBLEMA DA FOTO) ---
    print(f"   > Salvando {len(lista_final_elenco)} entradas únicas no ELENCO...")
    for jogador in lista_final_elenco:
        # Usamos INSERT OR IGNORE para evitar erro se a chave UNIQUE(id_time, nome_jogador) já existir
        cursor.execute('''
            INSERT OR IGNORE INTO elenco 
            (id_jogador, id_time, nome_jogador, numero, posicao, url_foto) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (jogador['id_jogador'], jogador['id_time'], jogador['nome_jogador'], 
              jogador['numero'], jogador['posicao'], jogador['url_foto']))

    # --- 3. ATLETAS (Geral) - Mantido do seu código original ---
    print(f"   > Atualizando {len(estatisticas_jogadores)} atletas (Dados CBF)...")
    for atleta_id, dados_atleta in estatisticas_jogadores.items():
        rodada_suspensao = dados_atleta.get('rodada_suspensao_amarelo', 0)
        
        cursor.execute('INSERT OR REPLACE INTO atletas (id, apelido, cartoes_amarelos, cartoes_vermelhos, rodada_ultimo_vermelho, rodada_suspensao_amarelo, time_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (atleta_id, dados_atleta['nome'], dados_atleta['amarelos'], dados_atleta['vermelhos'], dados_atleta['rodada_ultimo_vermelho'], rodada_suspensao, dados_atleta['time_id']))
    
    # --- 4. ESTATÍSTICAS TIME ---
    print(f"   > Salvando {len(estatisticas_times)} estatísticas de times...")
    for time_id, stats in estatisticas_times.items():
        cursor.execute('''
                INSERT OR REPLACE INTO estatisticas_time 
                (time_id, posicao, pontos, ultimos_jogos, media_cartoes_amarelos, total_cartoes_vermelhos, media_escanteios) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                time_id, 
                stats.get('posicao'), 
                stats.get('pontos'), 
                stats.get('ultimos_jogos'), 
                stats.get('media_amarelos', 0.0),      # Valor do main_run
                stats.get('total_vermelhos', 0),       # Valor do main_run
                stats.get('media_escanteios', 0.0)     # Valor do main_run
            ))

    # --- 5. PARTIDAS (Cabeçalho) ---
    print(f"   > Salvando {len(todas_as_partidas_info)} partidas...")
    for jogo in todas_as_partidas_info:
        cursor.execute('''INSERT OR REPLACE INTO partidas (
            id_jogo, rodada, data, hora, local, mandante_id, mandante_url_escudo, mandante_gols, mandante_formacao, 
            visitante_id, visitante_url_escudo, visitante_gols, visitante_formacao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (jogo['id_jogo'], jogo['rodada'], jogo.get('data'), jogo.get('hora', '00:00'), 'Local Desconhecido', 
             jogo.get('mandante_id'), jogo.get('mandante_url_escudo'), jogo.get('mandante_gols', '0'), jogo.get('mandante_formacao'),
             jogo.get('visitante_id'), jogo.get('visitante_url_escudo'), jogo.get('visitante_gols', '0'), jogo.get('visitante_formacao')))

    # --- 6. JOGOS FINALIZADOS ---
    print(f"   > Registrando {len(jogos_finalizados_info)} jogos finalizados...")
    for jogo in jogos_finalizados_info:
         cursor.execute("INSERT OR REPLACE INTO jogos_finalizados (id_jogo, rodada) VALUES (?, ?)", 
                        (jogo['id_jogo'], jogo['rodada']))


    # --- 7. PARTIDAS_ELENCO (LIGAÇÃO DE ESCALAÇÃO) ---
    print("   > Populando a tabela de ligação PARTIDAS_ELENCO...")
    
    # Criar um mapa de lookup rápido: (id_time_cbf, nome_jogador_normalizado) -> id_jogador_mestre
    mapa_lookup_elenco = {
        (e['id_time'], unidecode(e['nome_jogador']).lower().strip()): e['id_jogador'] 
        for e in lista_final_elenco
    }
    
    # Mapeamento reverso CBF para ID
    nome_cbf_para_id_cbf = {info['nome']: time_id for time_id, info in times_info.items()}

    for jogo_id, escalacao_data in todas_as_escalacoes.items():
        
        def inserir_ligacao(time_data, time_id_cbf, jogo_id):
            if not time_data: return
            
            for papel_lista, papel_mestre in [('titulares', 'TITULAR'), ('reservas', 'RESERVA'), ('fora_de_jogo', 'AUSENTE')]:
                for jogador in time_data.get(papel_lista, []):
                    nome_norm = unidecode(jogador['nome']).lower().strip()
                    
                    id_jogador_mestre = mapa_lookup_elenco.get((time_id_cbf, nome_norm))
                    
                    if id_jogador_mestre:
                        pos_x = jogador.get('pos_x') if papel_mestre == 'TITULAR' else None
                        pos_y = jogador.get('pos_y') if papel_mestre == 'TITULAR' else None
                        motivo = jogador.get('motivo', '') if papel_mestre == 'AUSENTE' else ''
                        
                        # ATENÇÃO: Esta inserção usa a estrutura de dados retornada pela PARTE III (antes da consolidação do ELENCO MESTRE)
                        cursor.execute('''
                            INSERT INTO partidas_elenco (jogo_id, id_time, id_jogador, papel, pos_x, pos_y, motivo) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (jogo_id, time_id_cbf, id_jogador_mestre, papel_mestre, pos_x, pos_y, motivo))

        # Processa os dados de escalação brutos (que contêm os X/Y e o motivo)
        if 'mandante' in escalacao_data:
            mandante_nome_cbf = escalacao_data['mandante'].get('nome_cbf_original')
            id_mandante = nome_cbf_para_id_cbf.get(mandante_nome_cbf)
            inserir_ligacao(escalacao_data['mandante'], id_mandante, jogo_id)
            
        if 'visitante' in escalacao_data:
            visitante_nome_cbf = escalacao_data['visitante'].get('nome_cbf_original')
            id_visitante = nome_cbf_para_id_cbf.get(visitante_nome_cbf)
            inserir_ligacao(escalacao_data['visitante'], id_visitante, jogo_id)

    # --- FINALIZAÇÃO ---
    conn.commit()
    conn.close()
    print("✅ Dados salvos/atualizados com sucesso em todas as tabelas, incluindo ELENCO.")

# ==============================================================================
# PARTE II (Refatorada) - Funções de Scraping
# ==============================================================================

def handle_cookie_banner(driver):
    """Tenta aceitar o banner de cookies da Didomi."""
    try:
        wait = WebDriverWait(driver, 5)
        agree_button = wait.until(EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button")))
        driver.execute_script("arguments[0].click();", agree_button)
        print("   > Banner de cookie aceito.")
        time.sleep(2)
    except Exception:
        pass

def handle_ad_popup(driver):
    """Tenta fechar pop-ups de propaganda."""
    try:
        wait = WebDriverWait(driver, 3)
        close_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'external-ad_close_button')]")))
        driver.execute_script("arguments[0].click();", close_button)
        print("   > Popup de propaganda fechado.")
        time.sleep(1)
    except Exception:
        pass

def buscar_classificacao_com_scraping(ano_competicao, times_info):
    """
    Realiza web scraping da tabela de classificação da CBF, mapeando os nomes
    encontrados para os IDs da API.
    (Lógica original mantida, pois não interfere no problema da foto)
    """
    print("\nBuscando dados de classificação via Web Scraping da CBF...")
    estatisticas_times = {}
    url_tabela = f"https://www.cbf.com.br/futebol-brasileiro/tabelas/campeonato-brasileiro/serie-a/{ano_competicao}"
    
    # --------------------------------------------------------------------------
    # 1. CRIAÇÃO DO MAPA DE BUSCA (API ID -> CHAVE NORMALIZADA)
    # --------------------------------------------------------------------------
    mapa_api_normalizado = {}
    for time_id, info in times_info.items():
        nome_cbf_api = info['nome']
        
        # 1. Traduz o nome longo da API para o nome curto (ex: 'Atlético Mineiro Saf' -> 'Atlético-MG')
        nome_curto_site = MAPA_NORMALIZACAO_NOME_CBF_SITE.get(nome_cbf_api, nome_cbf_api)
        
        # 2. Normalização Final Simétrica (Remove acentos, minúsculas, limpa)
        chave_de_busca = unidecode(nome_curto_site).lower().strip()
        chave_de_busca = chave_de_busca.replace(' saf', '').replace('s.a.f.', '').replace(' ec', '').replace(' fc', '').strip()
        chave_de_busca = re.sub(r'[.,-]', '', chave_de_busca) # Remove pontos, vírgulas, hífens
        chave_de_busca = chave_de_busca.replace(' ', '') # Remove todos os espaços (chave mais limpa)

        mapa_api_normalizado[chave_de_busca] = time_id
    # --------------------------------------------------------------------------

    try:
        response = requests.get(url_tabela, headers=HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        container_tabela = soup.find('div', class_='styles_tableContent__dh0gO')
        
        if not container_tabela:
            print("   > ERRO: Container da tabela de classificação não encontrado.")
            return {}
        
        tabela = container_tabela.find('table')
        if not tabela:
            print("   > ERRO: Tabela (tag <table>) não encontrada dentro do container.")
            return {}
            
        linhas = tabela.find('tbody').find_all('tr')
        
        for linha in linhas:
            celulas = linha.find_all('td')
            if len(celulas) < 13: continue
                
            posicao_tag = celulas[0].find('strong')
            # Nome do time é o strong que não tem classes relacionadas a styles
            nome_time_tag = celulas[0].find('strong', class_=lambda c: c is None or 'styles' not in c)
            pontos_tag = celulas[1]
            jogos_tag = celulas[2]
            ultimos_jogos_container = celulas[12].find('div')
            
            if not all([posicao_tag, nome_time_tag, pontos_tag, jogos_tag, ultimos_jogos_container]):
                continue
            
            posicao = posicao_tag.text.strip()
            nome_time_completo = nome_time_tag.text.strip()
            pontos = pontos_tag.text.strip()
            jogos_disputados = int(jogos_tag.text.strip())
            
            # ----------------------------------------------------
            # 2. NORMALIZAÇÃO DO NOME LIDO NO SITE PARA BUSCA
            # ----------------------------------------------------
            nome_site_normalizado = unidecode(nome_time_completo).lower().strip()
            nome_site_normalizado = nome_site_normalizado.replace(' saf', '').replace('s.a.f.', '').replace(' ec', '').replace(' fc', '').strip()
            nome_site_normalizado = re.sub(r'[.,-]', '', nome_site_normalizado)
            nome_site_normalizado = nome_site_normalizado.replace(' ', '') # Remove todos os espaços
            
            # Tratamento Específico
            if 'redbullbragantino' in nome_site_normalizado:
                nome_site_normalizado = nome_site_normalizado.replace('redbull', 'rb') 
            if 'atleticomineiro' in nome_site_normalizado:
                nome_site_normalizado = 'atleticomg' 
            # ----------------------------------------------------
            
            time_id = mapa_api_normalizado.get(nome_site_normalizado)
            
            if time_id:
                # Extração dos Últimos Jogos (lógica de SVG mantida)
                ultimos_jogos_svgs = ultimos_jogos_container.find_all('svg')
                ultimos_jogos_str = "".join([
                    'V' if svg.find('circle') and svg.find('circle').get('fill') == '#24C796' else 
                    'E' if svg.find('circle') and svg.find('circle').get('fill') == '#B7B7B7' else 
                    'D' for svg in ultimos_jogos_svgs if svg.find('circle')
                ])
                
                estatisticas_times[time_id] = {
                    'posicao': int(posicao), 
                    'pontos': int(pontos), 
                    'ultimos_jogos': ultimos_jogos_str, 
                    'jogos_disputados': jogos_disputados
                }
        
        print(f"✅ Dados de classificação para {len(estatisticas_times)} times processados com sucesso.")
        return estatisticas_times
        
    except Exception as e:
        print(f"   > Erro ao fazer web scraping da tabela de classificação: {e}")
        return {}

def extrair_dados_time(widget_content):
    """
    Extrai dados de escalação (Titulares, Reservas, Ausentes) de um widget
    do 365Scores. Retorna os dados crus, sem a URL da foto.
    """
    dados = {'titulares': [], 'reservas': [], 'fora_de_jogo': [], 'formacao': ''}
    
    try:
        formacao_tag = widget_content.find('bdi', class_=lambda c: c and 'lineups-widget_status_text' in c)
        dados['formacao'] = formacao_tag.text.strip() if formacao_tag else ''
    except AttributeError:
        print("     - Aviso: Formação não encontrada.")
        
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
            nome_jogador = j_tag.find('div', class_=lambda c: c and 'field-formation_player_name' in c).text.strip()
            style = j_tag.get('style', '')
            left_match = re.search(r'left:\s*([\d.-]+)px', style)
            bottom_match = re.search(r'bottom:\s*([\d.-]+)px', style)
            
            pos_x_px = float(left_match.group(1)) if left_match else 0.0
            pos_y_px = float(bottom_match.group(1)) if bottom_match else 0.0

            dados['titulares'].append({
                'nome': nome_jogador,
                'numero': j_tag.find('div', class_=lambda c: c and 'field-formation_player_number_text' in c).text.strip(),
                'pos_x': (pos_x_px / container_width) * 100,
                'pos_y': (pos_y_px / container_height) * 100,
                'nome_normalizado': unidecode(nome_jogador).lower().strip()
            })
    print(f"     - {len(dados['titulares'])} titulares encontrados.")

    listas_jogadores = widget_content.find_all('div', class_=lambda c: c and 'players-list-container' in c)
    for lista in listas_jogadores:
        titulo_tag = lista.find(['h2', 'h3'], class_=lambda c: c and 'card-title_title' in c)
        if not titulo_tag: continue

        if 'Banco' in titulo_tag.text:
            reservas = lista.find_all('a', class_=lambda c: c and 'players-list-item' in c)
            for j in reservas:
                nome_jogador = j.find('div', class_=lambda c: c and 'players-list-item-player-name' in c).text.strip()
                num_div = j.find('div', class_=lambda c: c and 'players-list-item-player-number' in c)
                pos_tag = j.find('div', class_=lambda c: c and 'players-list-item-player-position' in c)
                dados['reservas'].append({
                    'nome': nome_jogador,
                    'numero': num_div.div.text.strip() if num_div and num_div.div else 'S/N',
                    'posicao': pos_tag.text.strip() if pos_tag else 'N/A',
                    'nome_normalizado': unidecode(nome_jogador).lower().strip()
                })
            print(f"     - {len(dados['reservas'])} reservas encontrados.")
        elif 'Fora do jogo' in titulo_tag.text:
            ausentes = lista.find_all('a', class_=lambda c: c and 'players-list-item' in c)
            for j in ausentes:
                nome_jogador = j.find('div', class_=lambda c: c and 'players-list-item-player-name' in c).text.strip()
                motivo = 'Indisponível'
                if j.find('div', class_=lambda c: c and 'suspension' in c): motivo = 'Suspenso'
                elif j.find('div', class_=lambda c: c and 'injuries' in c): motivo = 'Lesionado'
                pos_tag = j.find('div', class_=lambda c: c and 'players-list-item-player-position' in c)
                dados['fora_de_jogo'].append({
                    'nome': nome_jogador,
                    'posicao': pos_tag.text.strip() if pos_tag else 'N/A',
                    'motivo': motivo,
                    'nome_normalizado': unidecode(nome_jogador).lower().strip()
                })
            print(f"     - {len(dados['fora_de_jogo'])} jogadores fora de jogo encontrados.")
    return dados

def buscar_stats_365scores():
    """Busca estatísticas agregadas de times no 365Scores (Selenium)."""
    print("\nBuscando dados de estatísticas via Web Scraping do 365Scores...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    
    service = ChromeService(ChromeDriverManager().install())
    driver = None
    stats_365 = {}
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://www.365scores.com/pt-br/football/league/brasileirao-serie-a-113/stats")
        handle_cookie_banner(driver)

        print("   > Clicando na aba 'Times'...")
        times_button = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'secondary-tabs_tab_button') and text()='Times']")))
        driver.execute_script("arguments[0].click();", times_button)
        
        print("   > Aguardando tabelas carregarem...")
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//h2[text()='Gols por jogo']")))
        
        # ... (Lógica de expandir tabelas e scraping dos dados estatísticos) ...
        try:
            print("   > Procurando e clicando em TODOS os botões 'Ver mais'...")
            ver_mais_buttons = driver.find_elements(By.XPATH, "//div[contains(text(), 'Ver mais')]")
            for button in ver_mais_buttons:
                driver.execute_script("arguments[0].click();", button)
            print("   > Todas as listas expandidas. Aguardando expansão...")
            # Espera por um elemento comum para garantir que a página renderizou o conteúdo extra
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//*[text()='Grêmio']"))) 
        except:
            print("   > AVISO: Nenhum botão 'Ver mais' encontrado ou falha na expansão. Continuando...")

        soup = BeautifulSoup(driver.page_source, 'lxml')
        
        titulos = {"Escanteios por jogo": "media_escanteios", "Cartões Amarelos": "total_amarelos", "Cartões Vermelhos": "total_vermelhos"}
        for titulo_texto, stat_key in titulos.items():
            titulo_tag = soup.find('h2', string=titulo_texto)
            if not titulo_tag:
                print(f"   > AVISO: Tabela '{titulo_texto}' não encontrada.")
                continue

            container_geral = titulo_tag.find_parent('div', class_=lambda c: c and c.startswith('entity-stats-widget_content'))
            if not container_geral:
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
        print(f"   > ❌ Erro ao fazer web scraping de estatísticas: {e}")
        return {}
    finally:
        if driver:
            driver.quit()
            print("   > Navegador de estatísticas fechado.")

# ==============================================================================
# PARTE III (Refatorada) - Funções de Elenco e Escalação
# ==============================================================================

def buscar_fotos_jogadores(driver):
    """
    Busca URLs de fotos de jogadores de todos os times e usa uma chave composta 
    (nome_time_normalizado_nome_jogador_normalizado) para evitar colisões.
    """
    print("\nBuscando fotos dos jogadores de todos os times...")
    fotos_por_chave = {} # Chave: nome_time_normalizado_nome_jogador_normalizado
    wait = WebDriverWait(driver, 10)
    for team_name, url in URLS_ELENCO_365.items():
        try:
            print(f"   > Buscando elenco do {team_name}...")
            driver.get(url)
            wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'squad-widget_row__')]")))
            time.sleep(2)
            
            soup = BeautifulSoup(driver.page_source, 'lxml')
            
            jogadores_tags = soup.find_all('a', class_=lambda c: c and 'squad-widget_row__' in c)
            count = 0
            
            # NORMALIZAÇÃO DO NOME DO TIME (Usada como prefixo da chave)
            nome_time_normalizado = unidecode(team_name).strip().lower().replace(' ', '_').replace('-', '_')
            
            for jogador_tag in jogadores_tags:
                nome_tag = jogador_tag.find('span', class_=lambda c: c and 'squad-widget_player_name__' in c)
                img_tag = jogador_tag.find('img', class_=lambda c: c and 'squad-widget_athlete_logo__' in c)
                
                if nome_tag and img_tag and img_tag.has_attr('src'):
                    nome_jogador_normalizado = unidecode(nome_tag.text.strip().lower())
                    foto_url = img_tag['src']
                    
                    if nome_jogador_normalizado and foto_url:
                        # CRIAÇÃO DA CHAVE COMPOSTA (CHAVE QUE RESOLVE O CONFLITO DE NOME)
                        chave_unica = f"{nome_time_normalizado}_{nome_jogador_normalizado}"
                        
                        # O MAPA_ABREVIACOES é usado para o nome do time. Aqui usaremos o team_name
                        nome_time_abreviado = MAPA_ABREVIACOES.get(team_name, team_name)
                        
                        fotos_por_chave[chave_unica] = foto_url
                        count += 1
                        
            print(f"     - {count} fotos de jogadores encontradas para {team_name}.")
        except Exception as e:
            print(f"     - ❌ Erro ao buscar elenco do {team_name}: {e}")
            continue
            
    print(f"\n✅ Total de {len(fotos_por_chave)} fotos de jogadores coletadas.")
    return fotos_por_chave

def buscar_escalacoes_da_rodada(proxima_rodada, jogos_da_proxima_rodada_cbf, mapa_nomes_cbf_para_365):
    """
    Busca escalações prováveis para a próxima rodada. Retorna a escalação 
    bruta e os nomes normalizados para posterior mapeamento de foto.
    """
    print(f"\nBuscando escalações para a rodada {proxima_rodada} no 365Scores...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    
    service = ChromeService(ChromeDriverManager().install())
    driver = None
    todas_as_escalacoes = {}

    try:
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 20)
        
        url_fixtures = "https://www.365scores.com/pt-br/football/league/brasileirao-serie-a-113/matches#fixtures"
        driver.get(url_fixtures)
        handle_cookie_banner(driver)
        
        print("   > Desenrolando o papiro de jogos para carregar todas as rodadas...")
        # Lógica de scroll para carregar todos os jogos (mantida)
        last_height = 0
        max_scrolls = 15 
        for i in range(max_scrolls):
            driver.execute_script("window.scrollBy(0, window.innerHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print(f"   > Fim da página alcançado na rolagem #{i+1}. Todos os jogos devem estar carregados.")
                break
            last_height = new_height
        
        # Lógica de mapeamento de URLs (mantida)
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
        
        print(f"   > {len(mapa_jogo_para_url)} URLs de jogos mapeadas para a rodada {proxima_rodada}.")

        # Iteração sobre os jogos da rodada
        for i, jogo_cbf in enumerate(jogos_da_proxima_rodada_cbf):
            print(f"\n--- Processando Jogo {i+1}/{len(jogos_da_proxima_rodada_cbf)} da Rodada {proxima_rodada} ---")
            
            nome_mandante_365 = mapa_nomes_cbf_para_365.get(jogo_cbf['mandante_nome'])
            nome_visitante_365 = mapa_nomes_cbf_para_365.get(jogo_cbf['visitante_nome'])

            if not (nome_mandante_365 and nome_visitante_365):
                print(f"   > AVISO: Nomes não mapeados para: {jogo_cbf['mandante_nome']} vs {jogo_cbf['visitante_nome']}. Pulando.")
                continue
            
            # Normalização do nome para a CHAVE DA FOTO
            nome_mandante_365_chave = unidecode(nome_mandante_365).strip().lower().replace(' ', '_').replace('-', '_')
            nome_visitante_365_chave = unidecode(nome_visitante_365).strip().lower().replace(' ', '_').replace('-', '_')

            chave_jogo_atual = f"{nome_mandante_365}-{nome_visitante_365}"
            url_jogo_365 = mapa_jogo_para_url.get(chave_jogo_atual)

            if not url_jogo_365:
                print(f"   > AVISO: URL não encontrada para o jogo {chave_jogo_atual}. Pulando.")
                continue

            print(f"   > URL do jogo: {url_jogo_365}")
            
            try:
                driver.get(url_jogo_365)
                handle_cookie_banner(driver)
                handle_ad_popup(driver)

                print("     - Clicando em 'Escalação provável'...")
                escalacao_tab = wait.until(EC.element_to_be_clickable((By.ID, "navigation-tabs_game-center_lineups")))
                driver.execute_script("arguments[0].click();", escalacao_tab)
                
                xpath_campo_futebol = "//div[contains(@class, 'game-center-widget_content')]//div[contains(@class, 'field-formation_field_container')]"
                wait.until(EC.presence_of_element_located((By.XPATH, xpath_campo_futebol)))
                time.sleep(1)

                jogo_atual = {'id_jogo': jogo_cbf['id_jogo']}

                # ----------------------------------------------------
                # EXTRAÇÃO MANDANTE
                # ----------------------------------------------------
                print(f"     - Extraindo dados de: {nome_mandante_365} (Mandante)")
                soup_mandante = BeautifulSoup(driver.page_source, 'lxml')
                widget_content_mandante = soup_mandante.find('div', class_=lambda c: c and 'game-center-widget_content' in c)
                if widget_content_mandante:
                    dados_mandante_brutos = extrair_dados_time(widget_content_mandante)
                    
                    # Adiciona chaves de mapeamento para o main_run
                    dados_mandante_brutos['nome_cbf_original'] = jogo_cbf['mandante_nome']
                    dados_mandante_brutos['chave_foto_prefixo'] = nome_mandante_365_chave
                    jogo_atual['mandante'] = dados_mandante_brutos

                # ----------------------------------------------------
                # EXTRAÇÃO VISITANTE
                # ----------------------------------------------------
                botoes_time = driver.find_elements(By.XPATH, "//div[contains(@class, 'secondary-tabs_tab_button_container')]")
                if len(botoes_time) > 1:
                    # Clica no segundo botão (Visitante)
                    driver.execute_script("arguments[0].click();", botoes_time[1])
                    time.sleep(3)
                    
                    print(f"     - Extraindo dados de: {nome_visitante_365} (Visitante)")
                    soup_visitante = BeautifulSoup(driver.page_source, 'lxml')
                    widget_content_visitante = soup_visitante.find('div', class_=lambda c: c and 'game-center-widget_content' in c)
                    if widget_content_visitante:
                        dados_visitante_brutos = extrair_dados_time(widget_content_visitante)
                        
                        # Adiciona chaves de mapeamento para o main_run
                        dados_visitante_brutos['nome_cbf_original'] = jogo_cbf['visitante_nome']
                        dados_visitante_brutos['chave_foto_prefixo'] = nome_visitante_365_chave
                        jogo_atual['visitante'] = dados_visitante_brutos
                
                todas_as_escalacoes[jogo_cbf['id_jogo']] = jogo_atual

            except Exception:
                print("   > Por enquanto, não temos nenhuma escalação disponível para esse jogo.")
                print(f"     - (Jogo: {nome_mandante_365} vs {nome_visitante_365})")
                continue

        return todas_as_escalacoes

    except Exception as e:
        print(f"   > ❌ Erro ao buscar escalações da rodada: {e}")
        return todas_as_escalacoes
    finally:
        if driver:
            driver.quit()
            print("   > Navegador de escalações fechado.")

def buscar_identidade_times_365scores(mapa_nomes_365_para_cbf):
    """
    Realiza web scraping no 365Scores para obter nomes abreviados, URLs de escudo
    e mapeá-los para o nome longo da CBF.
    """
    print("\nBuscando nomes e URLs de escudos dos times no 365Scores...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    
    service = ChromeService(ChromeDriverManager().install())
    driver = None
    identidades = {} # {nome_cbf_longo: {'nome_365_abreviado': '...', 'escudo_url': '...'}}
    
    URL_STANDINGS = "https://www.365scores.com/pt-br/football/league/brasileirao-serie-a-113/standings"

    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(URL_STANDINGS)
        handle_cookie_banner(driver)
        
        XPATH_TABELA = "//div[contains(@class, 'standings-widget_container')]"
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, XPATH_TABELA)))
        time.sleep(2) 
        
        soup = BeautifulSoup(driver.page_source, 'lxml')
        tabela_tag = soup.find('div', class_=lambda c: c and 'standings-widget_container' in c)
        
        if not tabela_tag:
            print("   > AVISO: Tabela de classificação não encontrada no 365Scores.")
            return {}
            
        linhas = tabela_tag.find_all('tr', class_=lambda c: c and 'standings-widget_table_row' in c)

        for linha in linhas:
            nome_tag = linha.find('div', class_=lambda c: c and 'competitor_name_text' in c)
            img_tag = linha.find('img', class_=lambda c: c and 'competitor_logo' in c)
            
            if nome_tag and img_tag and img_tag.has_attr('src'):
                nome_time_365 = nome_tag.text.strip()
                escudo_url = img_tag['src']
            
                nome_abreviado = MAPA_ABREVIACOES.get(nome_time_365, nome_time_365)
                nome_time_cbf = mapa_nomes_365_para_cbf.get(nome_time_365)
                
                # Tratamento manual de exceções
                if not nome_time_cbf:
                    if nome_time_365 == "America-MG":
                        nome_time_cbf = "América SAF"
                    elif nome_time_365 == "RB Bragantino":
                        nome_time_cbf = "Red Bull Bragantino"
                    
                    if not nome_time_cbf:
                        print(f"   > AVISO: Time '{nome_time_365}' (365Scores) não pode ser mapeado. Pulando.")
                        continue
                
                # Salva usando o Nome Longo CBF como chave
                identidades[nome_time_cbf] = {
                    'nome_365_abreviado': nome_abreviado,
                    'escudo_url': escudo_url
                }
        
        print(f"✅ Identidade (Nome/Escudo) de {len(identidades)} times coletadas com sucesso.")
        return identidades
        
    except Exception as e:
        print(f"   > ❌ Erro ao buscar nomes e escudos: {type(e).__name__}: {e}")
        return {}
    finally:
        if driver:
            driver.quit()
            print("   > Navegador de identidade de times fechado.")
            
# ==============================================================================
# FUNÇÃO PRINCIPAL (Refatorada)
# ==============================================================================

from datetime import datetime
import sys
# Importações necessárias (assumindo que já existem:
# from selenium import webdriver
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.chrome.service import Service as ChromeService
# ... outras funções e constantes ...

def main_run():
    print(f"\n{'='*20} INICIANDO CICLO DE COLETA - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} {'='*20}")
    
    # 🚨 PONTO DE ATENÇÃO: NÃO USAR criar_banco_de_dados() COM DROP TABLE AQUI. 
    # Mantenha a criação de tabelas se não existirem, mas evite o DROP/CREATE completo.
    criar_banco_de_dados()
    
    # 1. BUSCA DE DADOS BÁSICOS DA CBF (API)
    dados_jogadores, dados_times_cbf, jogos_finalizados, todas_as_partidas = buscar_dados_campeonato_completo(ID_COMPETICAO_CBF, TOTAL_RODADAS)
    
    if len(dados_times_cbf) < 2: 
        print(f"❌ ERRO: API da CBF retornou apenas {len(dados_times_cbf)} times. Encerrando.")
        sys.exit()

    # 2. BUSCA DA CLASSIFICAÇÃO CBF (Scraping)
    estatisticas_dos_times = buscar_classificacao_com_scraping(ANO_COMPETICAO, dados_times_cbf)
    if len(estatisticas_dos_times) < 2: 
        print(f"❌ ERRO GRAVE: Scraping da CBF retornou apenas {len(estatisticas_dos_times)} times. Continuando com cautela.")
    
    # 3. BUSCA DE ESTATÍSTICAS 365SCORES (Selenium)
    stats_365 = buscar_stats_365scores()

    # 4. ATUALIZAÇÃO DE NOMES E ESCUDOS DOS TIMES
    print("\n--- ATUALIZAÇÃO DE NOMES E ESCUDOS DOS TIMES ---")
    identidades_365 = buscar_identidade_times_365scores(MAPA_NOMES_365_PARA_CBF)
    nome_cbf_para_id = {info['nome']: time_id for time_id, info in dados_times_cbf.items()}
    
    if identidades_365:
        for nome_cbf_longo, identidade in identidades_365.items():
            time_id = nome_cbf_para_id.get(nome_cbf_longo)
            
            if time_id and time_id in dados_times_cbf:
                nome_a_salvar = identidade['nome_365_abreviado']
                dados_times_cbf[time_id]['nome_curto'] = nome_a_salvar
                dados_times_cbf[time_id]['nome'] = nome_a_salvar # Sobrescreve o nome longo da CBF
                dados_times_cbf[time_id]['url_escudo'] = identidade['escudo_url']
                
        # Mesclagem de Nome/Escudo Abreviado nas Partidas (Para o Flutter)
        for i, partida in enumerate(todas_as_partidas):
            mandante_id = partida.get('mandante_id') 
            visitante_id = partida.get('visitante_id')
            if mandante_id and mandante_id in dados_times_cbf:
                dados_mandante = dados_times_cbf[mandante_id]
                todas_as_partidas[i]['mandante_nome'] = dados_mandante['nome']
                todas_as_partidas[i]['mandante_url_escudo'] = dados_mandante.get('url_escudo', '')
            if visitante_id and visitante_id in dados_times_cbf:
                dados_visitante = dados_times_cbf[visitante_id]
                todas_as_partidas[i]['visitante_nome'] = dados_visitante['nome']
                todas_as_partidas[i]['visitante_url_escudo'] = dados_visitante.get('url_escudo', '')
    print("--- FIM DA ATUALIZAÇÃO ---")

    # ==============================================================================
    # 5. LÓGICA DE RODADA E BUSCA DE ESCALAÇÕES (Selenium)
    #    -> A chave para evitar a dessincronização é checar a última rodada salva.
    # ==============================================================================
    
    # Descobre qual é a rodada que a lógica CBF considera ser a próxima a começar
    rodada_cbf_sugerida = calcular_rodada_atual(jogos_finalizados, todas_as_partidas, TOTAL_RODADAS)
    
    # Lê do banco de dados qual foi a última rodada que salvamos escalações e elenco
    ultima_rodada_salva = ler_ultima_rodada_salva()
    
    # A rodada que vamos processar para buscar escalações é a maior entre a rodada salva 
    # e a rodada sugerida pela CBF. Isso garante que não voltemos.
    proxima_rodada = max(rodada_cbf_sugerida, ultima_rodada_salva + 1)
    
    print(f"🔄 Rodada sugerida pela CBF: {rodada_cbf_sugerida}")
    print(f"🔄 Última rodada salva com sucesso no banco: {ultima_rodada_salva}")
    print(f"➡️ Rodada escolhida para processamento de escalação: **{proxima_rodada}**")
    
    # Inicializa as variáveis de coleta
    todas_as_escalacoes = {}
    fotos_por_chave = {} 
    lista_final_elenco = [] 
    
    if proxima_rodada <= TOTAL_RODADAS:
        
        # INICIA O DRIVER PARA A COLETA DE FOTOS E O PASSA PARA A FUNÇÃO
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        service = ChromeService(ChromeDriverManager().install())
        driver_fotos = None
        
        try:
            # Inicialização do navegador para a coleta das URLs de fotos
            driver_fotos = webdriver.Chrome(service=service, options=options)
            # A função buscar_fotos_jogadores é o único lugar onde o driver é usado isoladamente para as fotos
            fotos_por_chave = buscar_fotos_jogadores(driver_fotos)
        except Exception as e:
            print(f"❌ ERRO ao iniciar driver para fotos: {e}")
        finally:
            if driver_fotos:
                driver_fotos.quit()
                print("   > Navegador de fotos fechado.")
                
        # Continua com a busca de escalações (que inicia seu próprio driver internamente)
        jogos_da_proxima_rodada_cbf = [jogo for jogo in todas_as_partidas if jogo['rodada'] == proxima_rodada]
        mapa_nomes_cbf_para_365 = {v: k for k, v in MAPA_NOMES_365_PARA_CBF.items()}
        todas_as_escalacoes = buscar_escalacoes_da_rodada(proxima_rodada, jogos_da_proxima_rodada_cbf, mapa_nomes_cbf_para_365)
        
    # 6. CRIAÇÃO DO ELENCO MESTRE E RESOLUÇÃO DE CONFLITO DE FOTOS
    print("\n--- GERAÇÃO DO ELENCO MESTRE (Tabela ELENCO) E RESOLUÇÃO DE CONFLITOS ---")
    elenco_mestre = {}
    jogador_id_counter = 1
    
    # Mapeamento {nome_cbf_original: id_cbf}
    nome_cbf_para_id_cbf = {info['nome']: time_id for time_id, info in dados_times_cbf.items()}

    for jogo_id, jogo_data in todas_as_escalacoes.items():
        
        # Funções aninhadas para processamento de jogadores
        def processar_jogador(jogador_data, time_id, chave_foto_prefixo, papel):
            nonlocal jogador_id_counter
            
            if not time_id: return
            
            nome_normalizado = jogador_data['nome_normalizado']
            chave_jogador_mestre = (time_id, nome_normalizado) # CHAVE ÚNICA (ID TIME, NOME JOGADOR)
            
            if chave_jogador_mestre not in elenco_mestre:
                # É a primeira vez que vemos este jogador
                chave_foto_365 = f"{chave_foto_prefixo}_{nome_normalizado}"
                foto_url = fotos_por_chave.get(chave_foto_365, '')
                
                elenco_mestre[chave_jogador_mestre] = {
                    "id_time": time_id,
                    "id_jogador": jogador_id_counter,
                    "nome_jogador": jogador_data['nome'],
                    "numero": jogador_data.get('numero', 'S/N'),
                    "posicao": jogador_data.get('posicao', papel).upper(),
                    "url_foto": foto_url,
                    "pos_x": jogador_data.get('pos_x') if papel == 'TITULAR' else None, 
                    "pos_y": jogador_data.get('pos_y') if papel == 'TITULAR' else None,
                    "motivo": jogador_data.get('motivo', '')
                }
                jogador_id_counter += 1
            else:
                # Se já existe (pode ter sido listado como reserva em outro jogo)
                if papel == 'TITULAR':
                    elenco_mestre[chave_jogador_mestre]['pos_x'] = jogador_data.get('pos_x')
                    elenco_mestre[chave_jogador_mestre]['pos_y'] = jogador_data.get('pos_y')
                    elenco_mestre[chave_jogador_mestre]['posicao'] = 'TITULAR'

        # Processamento Mandante
        if 'mandante' in jogo_data:
            mandante_nome_cbf = jogo_data['mandante']['nome_cbf_original']
            mandante_id = nome_cbf_para_id_cbf.get(mandante_nome_cbf)
            chave_prefixo = jogo_data['mandante']['chave_foto_prefixo']
            
            for j in jogo_data['mandante']['titulares']:
                processar_jogador(j, mandante_id, chave_prefixo, 'TITULAR')
            for j in jogo_data['mandante']['reservas']:
                processar_jogador(j, mandante_id, chave_prefixo, 'RESERVA')
            for j in jogo_data['mandante']['fora_de_jogo']:
                processar_jogador(j, mandante_id, chave_prefixo, 'AUSENTE')

        # Processamento Visitante
        if 'visitante' in jogo_data:
            visitante_nome_cbf = jogo_data['visitante']['nome_cbf_original']
            visitante_id = nome_cbf_para_id_cbf.get(visitante_nome_cbf)
            chave_prefixo = jogo_data['visitante']['chave_foto_prefixo']
            
            for j in jogo_data['visitante']['titulares']:
                processar_jogador(j, visitante_id, chave_prefixo, 'TITULAR')
            for j in jogo_data['visitante']['reservas']:
                processar_jogador(j, visitante_id, chave_prefixo, 'RESERVA')
            for j in jogo_data['visitante']['fora_de_jogo']:
                processar_jogador(j, visitante_id, chave_prefixo, 'AUSENTE')
    
    lista_final_elenco = list(elenco_mestre.values())
    print(f"✅ Elenco Mestre consolidado com {len(lista_final_elenco)} entradas únicas por Time/Jogador.")

    # 7. INJEÇÃO DE DADOS RESTANTES (Formação e Estatísticas 365)
    for jogo_id, escalacao_data in todas_as_escalacoes.items():
        for i, partida in enumerate(todas_as_partidas):
            if partida['id_jogo'] == jogo_id:
                if 'mandante' in escalacao_data and 'formacao' in escalacao_data['mandante']:
                    todas_as_partidas[i]['mandante_formacao'] = escalacao_data['mandante']['formacao']
                if 'visitante' in escalacao_data and 'formacao' in escalacao_data['visitante']:
                    todas_as_partidas[i]['visitante_formacao'] = escalacao_data['visitante']['formacao']
                break

    if estatisticas_dos_times and stats_365:
        # Mescla estatísticas 365Scores
        for nome_365, stats in stats_365.items():
            nome_cbf = MAPA_NOMES_365_PARA_CBF.get(nome_365, nome_365)
            time_id = nome_cbf_para_id_cbf.get(nome_cbf)
            
            if time_id and time_id in estatisticas_dos_times:
                jogos_disputados = estatisticas_dos_times[time_id].get('jogos_disputados', 0)
                total_amarelos = stats.get('total_amarelos', 0)
                estatisticas_dos_times[time_id]['media_amarelos'] = round(float(total_amarelos) / jogos_disputados, 2) if jogos_disputados > 0 else 0
                estatisticas_dos_times[time_id]['total_vermelhos'] = stats.get('total_vermelhos', 0)
                estatisticas_dos_times[time_id]['media_escanteios'] = stats.get('media_escanteios', 0)
                            
    # 8. SALVAMENTO FINAL E ATUALIZAÇÃO DO STATUS DA RODADA
    salvar_dados_no_banco(dados_jogadores, dados_times_cbf, jogos_finalizados, todas_as_partidas, estatisticas_dos_times, todas_as_escalacoes, lista_final_elenco)
    
    # Se a coleta e o salvamento foram bem-sucedidos para a rodada, registramos o status.
    if proxima_rodada <= TOTAL_RODADAS:
        salvar_ultima_rodada_processada(proxima_rodada)
    
    print(f"\n✅ CICLO CONCLUÍDO COM SUCESSO. {len(lista_final_elenco)} jogadores únicos salvos na tabela ELENCO.")

if __name__ == "__main__":
    main_run()