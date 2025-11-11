import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:path/path.dart' as p;
import '../models/campeonato_data.dart';
import '../models/classificacao_time.dart';
import '../models/escalacao.dart';
import '../models/jogador.dart';
import '../models/jogo.dart';
import '../models/time.dart';
import '../models/time_estatisticas.dart';

class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;
  DatabaseHelper._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB();
    return _database!;
  }

  Future<Database> _initDB() async {
    Directory documentsDirectory = await getApplicationDocumentsDirectory();
    final path = p.join(documentsDirectory.path, 'brasileirao.db');
    
    print("Abrindo banco de dados em: $path");
    return await openDatabase(path, version: 1);
  }

  Future<int> getRodadaAtual() async {
    final db = await instance.database;
    final result = await db.rawQuery('SELECT MAX(rodada) as rodada_atual FROM jogos_finalizados');
    if (result.isNotEmpty && result.first['rodada_atual'] != null) {
      return result.first['rodada_atual'] as int;
    }
    return 0;
  }
  
  Future<CampeonatoData> getCampeonatoData() async {
    final db = await instance.database;
    final int rodadaAtual = await getRodadaAtual();
    final result = await db.rawQuery('SELECT a.*, t.nome as time_nome, t.url_escudo FROM atletas a JOIN times t ON a.time_id = t.id WHERE a.cartoes_amarelos > 0 OR a.cartoes_vermelhos > 0 ORDER BY t.nome, a.apelido');
    final jogadores = result.map((json) => Jogador(
      apelido: json['apelido'] as String,
      timeNome: json['time_nome'] as String,
      urlEscudo: json['url_escudo'] as String?,
      totalAmarelos: json['cartoes_amarelos'] as int,
      totalVermelhos: json['cartoes_vermelhos'] as int,
      rodadaUltimoVermelho: json['rodada_ultimo_vermelho'] as int,
      rodadaSuspensaoAmarelo: json['rodada_suspensao_amarelo'] as int,
      rodadaAtual: rodadaAtual,
    )).toList();
    return CampeonatoData(jogadores: jogadores, rodadaAtual: rodadaAtual);
  }

  Future<List<Jogo>> getJogosDaRodada(int rodada) async {
    final db = await instance.database;
    final result = await db.query('partidas', where: 'rodada = ?', whereArgs: [rodada], orderBy: 'data');
    return result.map((json) => Jogo(id: json['id_jogo'] as int, rodada: json['rodada'] as int, data: json['data'] as String?, hora: json['hora'] as String?, local: json['local'] as String?, mandanteNome: json['mandante_nome'] as String?, mandanteEscudo: json['mandante_url_escudo'] as String?, mandanteGols: json['mandante_gols']?.toString(), visitanteNome: json['visitante_nome'] as String?, visitanteEscudo: json['visitante_url_escudo'] as String?, visitanteGols: json['visitante_gols']?.toString())).toList();
  }

  Future<List<Jogador>> getJogadoresPorTime(String timeNome) async {
    final db = await instance.database;
    final int rodadaAtual = await getRodadaAtual();
    final result = await db.rawQuery('SELECT a.*, t.nome as time_nome, t.url_escudo FROM atletas a JOIN times t ON a.time_id = t.id WHERE (a.cartoes_amarelos > 0 OR a.cartoes_vermelhos > 0) AND t.nome = ? ORDER BY a.apelido', [timeNome]);
    return result.map((json) => Jogador(
      apelido: json['apelido'] as String,
      timeNome: json['time_nome'] as String,
      urlEscudo: json['url_escudo'] as String?,
      totalAmarelos: json['cartoes_amarelos'] as int,
      totalVermelhos: json['cartoes_vermelhos'] as int,
      rodadaUltimoVermelho: json['rodada_ultimo_vermelho'] as int,
      rodadaSuspensaoAmarelo: json['rodada_suspensao_amarelo'] as int,
      rodadaAtual: rodadaAtual,
    )).toList();
  }
  
  Future<List<Jogador>> getJogadoresPenduradosParaJogo(String timeMandante, String timeVisitante) async {
    final db = await instance.database;
    final int rodadaAtual = await getRodadaAtual();
    final result = await db.rawQuery('SELECT a.*, t.nome as time_nome, t.url_escudo FROM atletas a JOIN times t ON a.time_id = t.id WHERE (t.nome = ? OR t.nome = ?) AND (a.cartoes_amarelos > 0 AND a.cartoes_amarelos % 3 = 2) ORDER BY t.nome, a.apelido', [timeMandante, timeVisitante]);
    return result.map((json) => Jogador(
      apelido: json['apelido'] as String,
      timeNome: json['time_nome'] as String,
      urlEscudo: json['url_escudo'] as String?,
      totalAmarelos: json['cartoes_amarelos'] as int,
      totalVermelhos: json['cartoes_vermelhos'] as int,
      rodadaUltimoVermelho: json['rodada_ultimo_vermelho'] as int,
      rodadaSuspensaoAmarelo: json['rodada_suspensao_amarelo'] as int,
      rodadaAtual: rodadaAtual,
    )).toList();
  }

  Future<List<Time>> getTodosOsTimes() async {
    final db = await instance.database;
    final result = await db.query('times', orderBy: 'nome');
    return result.map((json) => Time(id: json['id'] as int, nome: json['nome'] as String, urlEscudo: json['url_escudo'] as String?)).toList();
  }

  Future<List<ClassificacaoTime>> getTabelaClassificacao() async {
    final db = await instance.database;
    final result = await db.rawQuery('SELECT t.nome, t.url_escudo, e.posicao, e.pontos, e.ultimos_jogos FROM estatisticas_time e JOIN times t ON e.time_id = t.id WHERE e.posicao IS NOT NULL ORDER BY e.posicao ASC');
    return result.map((json) => ClassificacaoTime(nome: json['nome'] as String, urlEscudo: json['url_escudo'] as String?, posicao: json['posicao'] as int?, pontos: json['pontos'] as int?, ultimosJogos: json['ultimos_jogos'] as String?)).toList();
  }
  
  Future<Map<String, TimeEstatisticas>> getEstatisticasDosTimes(String mandanteNome, String visitanteNome) async {
    final db = await instance.database;
    final result = await db.rawQuery('SELECT t.nome, e.* FROM estatisticas_time e JOIN times t ON e.time_id = t.id WHERE t.nome = ? OR t.nome = ?', [mandanteNome, visitanteNome]);
    final Map<String, TimeEstatisticas> estatisticasMap = {};
    for (var json in result) {
      final timeNome = json['nome'] as String;
      estatisticasMap[timeNome] = TimeEstatisticas(
        posicao: json['posicao'] as int?,
        pontos: json['pontos'] as int?,
        ultimosJogos: json['ultimos_jogos'] as String?,
        mediaCartoesAmarelos: json['media_cartoes_amarelos'] as double?,
        totalCartoesVermelhos: json['total_cartoes_vermelhos'] as int?,
        mediaEscanteios: json['media_escanteios'] as double?,
      );
    }
    return estatisticasMap;
  }

  Future<JogoEscalacao?> getEscalacaoDoJogo(int jogoId, String mandanteNome, String visitanteNome) async {
    final db = await instance.database;

    final escalacoesResult = await db.query('escalacoes', where: 'jogo_id = ?', whereArgs: [jogoId]);
    if (escalacoesResult.isEmpty) {
      return null;
    }

    final partidasResult = await db.query('partidas', where: 'id_jogo = ?', whereArgs: [jogoId], limit: 1);
    final formacaoMandante = partidasResult.isNotEmpty ? partidasResult.first['mandante_formacao'] as String? : null;
    final formacaoVisitante = partidasResult.isNotEmpty ? partidasResult.first['visitante_formacao'] as String? : null;

    List<JogadorTitular> titularesMandante = [];
    List<JogadorReserva> reservasMandante = [];
    List<JogadorAusente> ausentesMandante = [];
    List<JogadorTitular> titularesVisitante = [];
    List<JogadorReserva> reservasVisitante = [];
    List<JogadorAusente> ausentesVisitante = [];

    for (var json in escalacoesResult) {
      final isTitular = json['is_titular'] == 1;
      final posicao = json['posicao'] as String?;
      
      // >>> CÓDIGO MELHORADO: Removemos a lógica de extração do motivo que era desnecessária e incompleta. <<<
      
      // Consideramos ausente se a posição contiver qualquer termo indicando indisponibilidade.
      final isAusente = posicao != null && (
        posicao.contains('Ausente') || 
        posicao.contains('Lesionado') || 
        posicao.contains('Suspenso') ||
        posicao.contains('Fora') // Adicionando termos comuns, se necessário
      );

      // O JogadorAusente.fromJson fará a separação Posicao/Motivo.

      if (json['time_nome'] == mandanteNome) {
        if (isTitular) {
          titularesMandante.add(JogadorTitular.fromJson(json));
        } else if (isAusente) {
          ausentesMandante.add(JogadorAusente.fromJson(json));
        } else {
          reservasMandante.add(JogadorReserva.fromJson(json));
        }
      } else if (json['time_nome'] == visitanteNome) {
        if (isTitular) {
          titularesVisitante.add(JogadorTitular.fromJson(json));
        } else if (isAusente) {
          ausentesVisitante.add(JogadorAusente.fromJson(json));
        } else {
          reservasVisitante.add(JogadorReserva.fromJson(json));
        }
      }
    }

    return JogoEscalacao(
      mandante: TimeEscalacao(
        nome: mandanteNome,
        formacao: formacaoMandante ?? 'N/D',
        titulares: titularesMandante,
        reservas: reservasMandante,
        foraDeJogo: ausentesMandante,
      ),
      visitante: TimeEscalacao(
        nome: visitanteNome,
        formacao: formacaoVisitante ?? 'N/D',
        titulares: titularesVisitante,
        reservas: reservasVisitante,
        foraDeJogo: ausentesVisitante,
      ),
    );
  }
}