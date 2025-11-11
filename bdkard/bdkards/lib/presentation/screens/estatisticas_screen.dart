import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import '../../data/database/database_helper.dart';
import '../../data/models/escalacao.dart';
import '../../data/models/jogo.dart';
import '../../data/models/time_estatisticas.dart';
import '../widgets/info_widgets.dart'; // Assumindo que este é o caminho correto

// =========================================================================
// ESTATISTICAS SCREEN
// =========================================================================

class EstatisticasScreen extends StatefulWidget {
  final Jogo jogo;
  const EstatisticasScreen({super.key, required this.jogo});

  @override
  State<EstatisticasScreen> createState() => _EstatisticasScreenState();
}

class _EstatisticasScreenState extends State<EstatisticasScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Pré-jogo'),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
      ),
      body: Column(
        children: [
          _StatsHeader(jogo: widget.jogo),
          Container(
            color: Colors.black.withOpacity(0.5),
            child: TabBar(
              controller: _tabController,
              labelColor: Colors.white,
              unselectedLabelColor: Colors.grey[400],
              indicatorColor: Colors.green,
              tabs: const [
                Tab(text: 'ESTATÍSTICAS'),
                Tab(text: 'ESCALAÇÃO'),
              ],
            ),
          ),
          Expanded(
            child: Container(
              color: Colors.black.withOpacity(0.5),
              child: TabBarView(
                controller: _tabController,
                children: [
                  _buildEstatisticasView(),
                  _buildEscalacaoView(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEstatisticasView() {
    return FutureBuilder<Map<String, TimeEstatisticas>>(
      future: DatabaseHelper.instance.getEstatisticasDosTimes(
        widget.jogo.mandanteNome ?? '',
        widget.jogo.visitanteNome ?? '',
      ),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError || !snapshot.hasData || snapshot.data!.isEmpty) {
          return const Center(child: Text('Estatísticas não disponíveis.', style: TextStyle(color: Colors.white)));
        }

        final stats = snapshot.data!;
        final mandanteStats = stats[widget.jogo.mandanteNome];
        final visitanteStats = stats[widget.jogo.visitanteNome];
        const textStyle = TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold);

        return ListView(
          padding: const EdgeInsets.all(16.0),
          children: [
            _StatRow(
              title: 'Últimos Jogos',
              mandanteValue: UltimosJogosWidget(resultado: mandanteStats?.ultimosJogos ?? ''),
              visitanteValue: UltimosJogosWidget(resultado: visitanteStats?.ultimosJogos ?? ''),
            ),
            _StatRow(title: 'Posição', mandanteValue: Text('${mandanteStats?.posicao ?? '-'}º', style: textStyle), visitanteValue: Text('${visitanteStats?.posicao ?? '-'}º', style: textStyle)),
            _StatRow(title: 'Pontuação', mandanteValue: Text('${mandanteStats?.pontos ?? '-'}', style: textStyle), visitanteValue: Text('${visitanteStats?.pontos ?? '-'}', style: textStyle)),
            _StatRow(title: 'Escanteios (Média)', mandanteValue: Text('${mandanteStats?.mediaEscanteios?.toStringAsFixed(1) ?? '-'}', style: textStyle), visitanteValue: Text('${visitanteStats?.mediaEscanteios?.toStringAsFixed(1) ?? '-'}', style: textStyle)),
            _StatRow(title: 'Cartões Amarelos (Média)', mandanteValue: Text('${mandanteStats?.mediaCartoesAmarelos?.toStringAsFixed(1) ?? '-'}', style: textStyle), visitanteValue: Text('${visitanteStats?.mediaCartoesAmarelos?.toStringAsFixed(1) ?? '-'}', style: textStyle)),
            _StatRow(title: 'Expulsões (Total)', mandanteValue: Text('${mandanteStats?.totalCartoesVermelhos ?? '-'}', style: textStyle), visitanteValue: Text('${visitanteStats?.totalCartoesVermelhos ?? '-'}', style: textStyle)),
          ],
        );
      },
    );
  }

  Widget _buildEscalacaoView() {
    return FutureBuilder<JogoEscalacao?>(
      future: DatabaseHelper.instance.getEscalacaoDoJogo(widget.jogo.id, widget.jogo.mandanteNome ?? '', widget.jogo.visitanteNome ?? ''),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Center(child: Text('Erro ao carregar escalação: ${snapshot.error}', style: const TextStyle(color: Colors.white)));
        }
        if (!snapshot.hasData || snapshot.data == null) {
          return const Center(
            child: Padding(
              padding: EdgeInsets.all(16.0),
              child: Text(
                'Por enquanto, não temos nenhuma escalação disponível para esse jogo.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.white70, fontSize: 16),
              ),
            ),
          );
        }

        final jogoEscalacao = snapshot.data!;
        
        return _AbaEscalacaoDetalhes(jogo: jogoEscalacao);
      },
    );
  }

}


// =========================================================================
// WIDGETS DE SUPORTE - HEADER
// =========================================================================

class _StatsHeader extends StatelessWidget {
  final Jogo jogo;
  const _StatsHeader({required this.jogo});
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      color: Colors.black.withOpacity(0.6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _TeamHeaderDisplay(nome: jogo.mandanteNome, escudoUrl: jogo.mandanteEscudo),
          Column(
            children: [
              Text(jogo.data ?? '', style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
              Text(jogo.hora ?? '', style: const TextStyle(color: Colors.white70)),
            ],
          ),
          _TeamHeaderDisplay(nome: jogo.visitanteNome, escudoUrl: jogo.visitanteEscudo),
        ],
      ),
    );
  }
}

class _TeamHeaderDisplay extends StatelessWidget {
  final String? nome;
  final String? escudoUrl;
  const _TeamHeaderDisplay({this.nome, this.escudoUrl});
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        if (escudoUrl != null)
          Image.network(escudoUrl!, height: 40, width: 40, errorBuilder: (c,e,s) => const Icon(Icons.shield, size: 40, color: Colors.white)),
        const SizedBox(height: 8),
        Text(nome ?? '?', style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
      ],
    );
  }
}

class _StatRow extends StatelessWidget {
  final String title;
  final Widget mandanteValue;
  final Widget visitanteValue;
  const _StatRow({required this.title, required this.mandanteValue, required this.visitanteValue});
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12.0),
      child: Row(
        children: [
          Expanded(flex: 2, child: Align(alignment: Alignment.centerLeft, child: mandanteValue)),
          Expanded(flex: 3, child: Text(title, textAlign: TextAlign.center, style: TextStyle(color: Colors.grey[300]))),
          Expanded(flex: 2, child: Align(alignment: Alignment.centerRight, child: visitanteValue)),
        ],
      ),
    );
  }
}


// =========================================================================
// WIDGETS DE SUPORTE - ESCALAÇÃO (Aba 2)
// =========================================================================

class _AbaEscalacaoDetalhes extends StatelessWidget {
  final JogoEscalacao jogo;
  const _AbaEscalacaoDetalhes({Key? key, required this.jogo}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Usamos DefaultTabController para as abas internas (mandante/visitante)
    return DefaultTabController(
      length: 2,
      child: Column(
        children: [
          Container(
            color: Colors.black.withOpacity(0.3),
            child: TabBar(
              indicatorColor: Colors.amberAccent,
              labelColor: Colors.white,
              unselectedLabelColor: Colors.grey[400],
              tabs: [
                Tab(text: jogo.mandante.nome.toUpperCase()),
                Tab(text: jogo.visitante.nome.toUpperCase()),
              ],
            ),
          ),
          Expanded(
            child: TabBarView(
              children: [
                _FootballPitchView(time: jogo.mandante),
                _FootballPitchView(time: jogo.visitante),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _FootballPitchView extends StatelessWidget {
  final TimeEscalacao time;
  const _FootballPitchView({required this.time});

  @override
  Widget build(BuildContext context) {
    if (time.titulares.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Text(
            'Escalação não disponível para este time.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 16, color: Colors.grey[400]),
          ),
        ),
      );
    }
    final double? minPosY = time.titulares.isNotEmpty 
        ? time.titulares.map((p) => p.posY).reduce((a, b) => a < b ? a : b)
        : null;
    
    final double? maxPosY = time.titulares.isNotEmpty
      ? time.titulares.map((p) => p.posY).reduce((a, b) => a > b ? a : b)
      : null;

    return SingleChildScrollView(
      child: Column(
        children: [
          const SizedBox(height: 12.0),
          ConstrainedBox(
            // CORRIGIDO: Sintaxe do ConstrainedBox
            constraints: const BoxConstraints(
              minWidth: 600, 
              minHeight: 400, 
            ),
            child: AspectRatio( // Agora é o child do ConstrainedBox
              aspectRatio: 1.5,
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final fieldWidth = constraints.maxWidth;
                  final fieldHeight = constraints.maxHeight;

                  final double fatorEncurtamento = 0.80; 
                  final double larguraEfetiva = fieldWidth * fatorEncurtamento;
                        // Calcula o offset para centralizar a formação encurtada
                  final double centralOffset = (fieldWidth - larguraEfetiva) / 2;


                  return Stack(
                    fit: StackFit.expand,
                    children: [
                      SvgPicture.network(
                        "https://imagecache.365scores.com/image/upload/f_svg,c_limit,q_auto:eco,dpr_1/website/AssetsSVGNewBrand/Lineups_Pitch",
                        fit: BoxFit.fill,
                        placeholderBuilder: (BuildContext context) => Container(
                          color: Colors.green[800],
                          child: const Center(child: CircularProgressIndicator(color: Colors.white))
                        ),
                      ),
                      ...time.titulares.map((player) {
                                      
                        // CORRIGIDO: Usa /90 e aplica o offset de centralização
                        double left = (player.posX / 90) * larguraEfetiva + centralOffset; 
                        double bottom = (player.posY / 115) * fieldHeight;

                        if (minPosY != null && player.posY == minPosY) {
                          bottom += fieldHeight * 0.09; 
                        }
                        if (maxPosY != null && player.posY == maxPosY) {
                          bottom -= fieldHeight * 0.08;
                        }
                        
                        return Positioned(
                          left: left,
                          bottom: bottom,
                          
                          // CORRIGIDO: O ajuste deve ser -30 (metade de 60px) para centralizar o ícone.
                          child: Transform.translate(
                            offset: const Offset(-30, -30), 
                            child: _PlayerMarker(player: player),
                          ),
                        );
                      }).toList(),
                    ],
                  );
                },
              ),
            ),
          ),
          // INÍCIO DO CÓDIGO CORRIGIDO (estava nas linhas com erro)
          if (time.formacao.isNotEmpty && time.formacao != 'N/D')
            Padding(
              padding: const EdgeInsets.only(top: 8.0, bottom: 16.0),
              child: Text(
                "Formação: ${time.formacao}",
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16, fontStyle: FontStyle.italic),
              ),
            ),
          
          if (time.reservas.isNotEmpty) ...[
            _SectionTitle('Reservas'),
            _ReservasList(jogadores: time.reservas),
          ],
          const SizedBox(height: 20),

          if (time.foraDeJogo.isNotEmpty) ...[
            _SectionTitle('Fora de Jogo'),
            _AusentesList(jogadores: time.foraDeJogo),
          ]
        ],
      ),
    );
  } // Fim do build da classe _FootballPitchView
} // Fim da classe _FootballPitchView

// =========================================================================
// WIDGETS DE SUPORTE - MARKER E LISTAS
// =========================================================================

class _PlayerMarker extends StatelessWidget {
  final JogadorTitular player;
  const _PlayerMarker({required this.player});

  @override
  Widget build(BuildContext context) {
    bool hasImage = player.fotoUrl.isNotEmpty;

    return SizedBox(
      width: 60, // Tamanho fixo para o jogador
      height: 60,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Stack(
            clipBehavior: Clip.none,
            children: [
              CircleAvatar(
                radius: 18,
                backgroundColor: Colors.black54,
                child: CircleAvatar(
                  radius: 16,
                  backgroundColor: Colors.grey.shade800,
                  backgroundImage: hasImage ? NetworkImage(player.fotoUrl) : null,
                  onBackgroundImageError: hasImage ? (e, s) {} : null,
                  child: !hasImage ? const Icon(Icons.person, size: 20, color: Colors.white70) : null,
                ),
              ),
              Positioned(
                top: -4,
                left: -4,
                child: CircleAvatar(
                  radius: 8,
                  backgroundColor: Colors.black.withOpacity(0.8),
                  child: Text(
                    player.numero,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 2),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
            decoration: BoxDecoration(
              color: Colors.black.withOpacity(0.7),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              player.nome,
              style: const TextStyle(color: Colors.white, fontSize: 8),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String title;
  const _SectionTitle(this.title);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12.0, vertical: 8.0),
      child: Align(
        alignment: Alignment.centerLeft,
        child: Text(
          title,
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.greenAccent[400]),
        ),
      ),
    );
  }
}

// ============== WIDGET RESERVAS (Mantido) ==============
class _ReservasList extends StatelessWidget {
  final List<JogadorReserva> jogadores;
  const _ReservasList({required this.jogadores});

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white.withOpacity(0.1),
      elevation: 0,
      margin: const EdgeInsets.symmetric(horizontal: 12.0),
      child: Column(
        children: jogadores.map((j) {
          bool hasImage = j.fotoUrl.isNotEmpty;
          
          // >>> AÇÃO CORRETIVA: Limpar o nome
          String nomeLimpo = j.nome.replaceAll(j.posicao, '').trim();
          if (nomeLimpo.isEmpty) {
            nomeLimpo = j.nome; // Fallback se a limpeza falhar
          }
          
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 10.0, horizontal: 16.0),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CircleAvatar(
                  radius: 16,
                  backgroundColor: Colors.grey[800],
                  backgroundImage: hasImage ? NetworkImage(j.fotoUrl) : null,
                  onBackgroundImageError: hasImage ? (e, s) {} : null,
                  child: !hasImage ? Text(j.numero, style: const TextStyle(color: Colors.white, fontSize: 12)) : null,
                ),
                const SizedBox(width: 12),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Usando o nome limpo
                    Text(nomeLimpo, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500)),
                    Text(j.posicao, style: TextStyle(color: Colors.grey[400], fontSize: 12)),
                  ],
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }
}


/// ============== WIDGET AUSENTES (CORRIGIDO) ==============

class _AusentesList extends StatelessWidget {

  final List<JogadorAusente> jogadores;
  const _AusentesList({required this.jogadores});

  // Lista combinada de posições (para priorizar as mais longas e específicas)
  static const List<String> posicoesCombinadas = [
    'Goleiro',
    'Zagueiro', 'Zagueiro Central',
    'Lateral Esquerdo', 'Lateral Direito',
    'Volante',
    'Meia', 'Meio de Campo Central', 'Meia Esquerda', "Meia Direita", 'Meia Atacante',  
    'Ponta', 'Ponta Direita', 'Ponta Esquerda',
    'Atacante', 'Centroavante', 
  ];
  
  // Função auxiliar para limpar e extrair a posição do nome (CORRIGIDA)
  Map<String, String> _splitNameAndPosition(String fullName) {
    String nomeLimpo = fullName.trim();
    String posicaoExtraida = 'N/A';

    // Ordena para garantir que tentamos remover "Meia Atacante" antes de "Meia" ou "Atacante"
    final posicoesOrdenadas = posicoesCombinadas
      .toList()..sort((a, b) => b.length.compareTo(a.length)); 

    for (String pos in posicoesOrdenadas) {
      // Cria um padrão de regex que encontra a posição como uma palavra completa ou no final da string
      final RegExp regex = RegExp('\\b$pos\\b|${pos}\$', caseSensitive: false);
      final match = regex.firstMatch(fullName);

      if (match != null) {
        // Encontrou a posição. Removemos do nome e salvamos a posição.
        nomeLimpo = fullName.replaceAll(RegExp(match.group(0)!, caseSensitive: false), '').trim();
        posicaoExtraida = match.group(0)!.trim(); // Salva a posição exata encontrada
        break; // Para após encontrar a melhor correspondência
      }
    }

    // Limpa espaços extras no nome
    nomeLimpo = nomeLimpo.replaceAll(RegExp(r'\s+'), ' ').trim();

    // Fallback se a limpeza deixar o nome vazio
    if (nomeLimpo.isEmpty) {
        nomeLimpo = fullName; 
        posicaoExtraida = 'N/A';
    }

    return {'nome': nomeLimpo, 'posicao': posicaoExtraida};
  }


  @override
  Widget build(BuildContext context) {
    if (jogadores.isEmpty) {
      return const Padding(
        padding: EdgeInsets.all(8.0),
        child: Text(
          'Nenhum jogador fora de jogo.',
          style: TextStyle(color: Colors.white70, fontStyle: FontStyle.italic),
          textAlign: TextAlign.center,
        ),
      );
    }

    return Card(
      color: Colors.white.withOpacity(0.1),
      elevation: 0,
      margin: const EdgeInsets.symmetric(horizontal: 12.0),
      child: Column(
        children: jogadores.map((j) {
          bool hasImage = j.fotoUrl.isNotEmpty;
          IconData icon;
          Color color;
          final motivoLower = j.motivo.toLowerCase();
          
          if (motivoLower.contains('suspenso')) {
            icon = Icons.style;
            color = Colors.orange.shade800;
          } else if (motivoLower.contains('lesionado')) {
            icon = Icons.medical_services_outlined;
            color = Colors.red.shade800;
          } else {
            icon = Icons.help_outline;
            color = Colors.grey;
          }

          // >>> AÇÃO CORRETIVA: Usa a função de separação melhorada
          final splitData = _splitNameAndPosition(j.nome);
          final String nomeExibido = splitData['nome']!;
          final String posicaoExibida = splitData['posicao']!;
          
          final String posicaoFinal = (j.posicao != 'N/A' && j.posicao.isNotEmpty && j.posicao != posicaoExibida) 
            ? j.posicao 
            : posicaoExibida;
          // <<< FIM DA LÓGICA DE SEPARAÇÃO

          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 10.0, horizontal: 16.0),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CircleAvatar(
                  radius: 16,
                  backgroundColor: Colors.grey.shade800,
                  backgroundImage: hasImage ? NetworkImage(j.fotoUrl) : null,
                  onBackgroundImageError: hasImage ? (e, s) {} : null,
                  child: !hasImage ? const Icon(Icons.person_off, size: 20, color: Colors.white70) : null,
                ),
                const SizedBox(width: 12),
                
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // Linha 1: Nome Limpo ("Paulo")
                      Text(nomeExibido, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                      
                      // Linha 2: Posição (Exibida SOMENTE se a posição for detectada)
                      if (posicaoFinal != 'N/A')
                        Text(
                          posicaoFinal, // "Meia Atacante"
                          style: TextStyle(color: Colors.white70, fontSize: 12, fontStyle: FontStyle.italic),
                        ),
                      
                      // Fallback: Exibe "Posição indisponível" se não achou nada
                      if (posicaoFinal == 'N/A')
                        Text(
                          'Posição: Indisponível',
                          style: TextStyle(color: Colors.white70, fontSize: 12, fontStyle: FontStyle.italic),
                        ),
                    ],
                  ),
                ),
                
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(icon, color: color, size: 16),
                    const SizedBox(width: 4),
                    Container(
                      constraints: const BoxConstraints(maxWidth: 100), 
                      child: Text(j.motivo, style: TextStyle(color: color, fontSize: 12)),
                    ),
                  ],
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }
}