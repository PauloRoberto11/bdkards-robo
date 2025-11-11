import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../data/database/database_helper.dart';
import '../../data/models/jogo.dart';
import '../../data/models/jogador.dart';
import 'time_detalhe_screen.dart';
import '../widgets/info_widgets.dart';
import 'estatisticas_screen.dart';

class JogosScreen extends StatefulWidget {
  const JogosScreen({super.key});

  @override
  State<JogosScreen> createState() => _JogosScreenState();
}

class _JogosScreenState extends State<JogosScreen> {
  int? _selectedRound;
  Future<List<Jogo>>? _jogosFuture;

  @override
  void initState() {
    super.initState();
    _initializeScreen();
  }

  Future<void> _initializeScreen() async {
    int rodadaInicial = await DatabaseHelper.instance.getRodadaAtual();
    if (mounted) {
      setState(() {
        _selectedRound = (rodadaInicial > 0) ? rodadaInicial : 1;
        _fetchJogosForSelectedRound();
      });
    }
  }

  void _fetchJogosForSelectedRound() {
    if (_selectedRound != null) {
      setState(() {
        _jogosFuture = DatabaseHelper.instance.getJogosDaRodada(_selectedRound!);
      });
    }
  }

  void _onRoundSelected(int? newRound) {
    if (newRound != null) {
      setState(() {
        _selectedRound = newRound;
        _fetchJogosForSelectedRound();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Jogos por Rodada')),
      body: Column(
        children: [
          FutureBuilder<int>(
            future: DatabaseHelper.instance.getRodadaAtual(),
            builder: (context, snapshot) {
              if (snapshot.hasData) {
                return InfoHeader(rodadaAtual: snapshot.data!);
              }
              return Container(width: double.infinity, color: Colors.transparent, padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 21.5), child: const Text(''));
            },
          ),
          _buildRoundSelector(),
          Expanded(
            child: _jogosFuture == null
                ? const Center(child: CircularProgressIndicator())
                : FutureBuilder<List<Jogo>>(
                    future: _jogosFuture,
                    builder: (context, snapshot) {
                      if (snapshot.connectionState == ConnectionState.waiting) {
                        return const Center(child: CircularProgressIndicator());
                      } else if (snapshot.hasError) {
                        return Center(child: Text('Erro: ${snapshot.error}', style: const TextStyle(color: Colors.white)));
                      } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
                        return const Center(child: Text('Nenhum jogo encontrado para esta rodada.', style: TextStyle(color: Colors.white)));
                      } else {
                        final jogos = snapshot.data!;
                        
                        return LayoutBuilder(
                          builder: (context, constraints) {
                            final bool isNarrow = constraints.maxWidth < 450;
                            final int crossAxisCount = isNarrow ? 1 : 2;
                            // ===== ALTURA RESPONSIVA AJUSTADA AQUI =====
                            final double childAspectRatio = isNarrow ? 2.0 : 1.2;

                            return GridView.builder(
                              padding: const EdgeInsets.all(8),
                              gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                                crossAxisCount: crossAxisCount,
                                childAspectRatio: childAspectRatio,
                                crossAxisSpacing: 4,
                                mainAxisSpacing: 4,
                              ),
                              itemCount: jogos.length,
                              itemBuilder: (context, index) {
                                return _JogoCard(jogo: jogos[index]);
                              },
                            );
                          },
                        );
                      }
                    },
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildRoundSelector() {
    if (_selectedRound == null) {
      return Container(padding: const EdgeInsets.symmetric(vertical: 25), child: const Center(child: Text("Carregando seletor...", style: TextStyle(color: Colors.white))));
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: Colors.black.withOpacity(0.3),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text('Selecionar Rodada:', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
          const SizedBox(width: 16),
          DropdownButton<int>(
            value: _selectedRound,
            dropdownColor: Colors.grey[800],
            style: const TextStyle(color: Colors.white),
            items: List.generate(38, (index) => index + 1).map((round) => DropdownMenuItem(value: round, child: Text('$round'))).toList(),
            onChanged: _onRoundSelected,
          ),
        ],
      ),
    );
  }
}

class _JogoCard extends StatelessWidget {
  final Jogo jogo;
  const _JogoCard({required this.jogo});

  void _navigateToTeamDetail(BuildContext context, String? timeNome) {
    if (timeNome == null) return;
    Navigator.push(context, MaterialPageRoute(builder: (context) => TimeDetalheScreen(timeNome: timeNome)));
  }

  void _showPenduradosDialog(BuildContext context) {
    if (jogo.mandanteNome == null || jogo.visitanteNome == null) return;
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return Dialog(
          backgroundColor: Colors.transparent,
          elevation: 0,
          child: Container(
            constraints: const BoxConstraints(maxHeight: 450),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(12.0),
              child: Stack(
                children: [
                  Positioned.fill(
                    child: Image.asset(
                      'assets/images/bk_app.jpg',
                      fit: BoxFit.cover,
                    ),
                  ),
                  Positioned.fill(
                    child: Container(color: Colors.black.withOpacity(0.8)),
                  ),
                  Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                        child: const Text('Pendurados para a Partida', textAlign: TextAlign.center, style: TextStyle(color: Colors.white, fontSize: 20)),
                      ),
                      Expanded(
                        child: FutureBuilder<List<Jogador>>(
                          future: DatabaseHelper.instance.getJogadoresPenduradosParaJogo(jogo.mandanteNome!, jogo.visitanteNome!),
                          builder: (context, snapshot) {
                            if (snapshot.connectionState == ConnectionState.waiting) {
                              return const Center(child: CircularProgressIndicator());
                            } else if (snapshot.hasError) {
                              return const Center(child: Text('Erro ao buscar jogadores.', style: TextStyle(color: Colors.white)));
                            } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
                              return const Center(child: Text('Nenhum jogador pendurado para esta partida.', style: TextStyle(color: Colors.white)));
                            }
                            final pendurados = snapshot.data!;
                            final mandantePendurados = pendurados.where((p) => p.timeNome == jogo.mandanteNome).toList();
                            final visitantePendurados = pendurados.where((p) => p.timeNome == jogo.visitanteNome).toList();
                            
                            // ===== PADDING REMOVIDO DAQUI =====
                            return Row(
                              children: [
                                Expanded(child: _PenduradosColumn(timeNome: jogo.mandanteNome!, escudoUrl: jogo.mandanteEscudo, jogadores: mandantePendurados, alignment: CrossAxisAlignment.start)),
                                VerticalDivider(color: Colors.white.withOpacity(0.5)),
                                Expanded(child: _PenduradosColumn(timeNome: jogo.visitanteNome!, escudoUrl: jogo.visitanteEscudo, jogadores: visitantePendurados, alignment: CrossAxisAlignment.end)),
                              ],
                            );
                          },
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.all(8.0),
                        child: TextButton(child: const Text('Fechar', style: TextStyle(color: Colors.white)), onPressed: () => Navigator.of(context).pop()),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  void _navigateToStats(BuildContext context) {
    Navigator.push(context, MaterialPageRoute(builder: (context) => EstatisticasScreen(jogo: jogo)));
  }

  @override
  Widget build(BuildContext context) {
    final bool jogoNaoIniciado = jogo.mandanteGols == null || jogo.mandanteGols!.trim().isEmpty;

    return Card(
      color: Colors.white.withOpacity(0.9),
      child: Padding(
        padding: const EdgeInsets.all(8.0),
        // ===== ROLAGEM INTERNA REMOVIDA =====
        child: Column(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            Text(
              '${jogo.data ?? 'Data indefinida'} - ${jogo.hora ?? ''}',
              style: TextStyle(color: Colors.grey[800], fontSize: 10),
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                _TeamDisplay(nome: jogo.mandanteNome ?? '?', escudoUrl: jogo.mandanteEscudo, onTap: () => _navigateToTeamDetail(context, jogo.mandanteNome)),
                Text('${jogo.mandanteGols ?? '-'} x ${jogo.visitanteGols ?? '-'}', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                _TeamDisplay(nome: jogo.visitanteNome ?? '?', escudoUrl: jogo.visitanteEscudo, onTap: () => _navigateToTeamDetail(context, jogo.visitanteNome)),
              ],
            ),
            const SizedBox(height: 8),
            if (jogoNaoIniciado)
              FittedBox(
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    TextButton.icon(
                      style: TextButton.styleFrom(padding: EdgeInsets.zero, visualDensity: VisualDensity.compact),
                      onPressed: () => _showPenduradosDialog(context),
                      label: const Text('Pendurados', style: TextStyle(fontSize: 10)),
                      icon: const Icon(Icons.warning_amber_rounded, color: Colors.orange, size: 14),
                    ),
                    const SizedBox(width: 8),
                    TextButton.icon(
                      style: TextButton.styleFrom(padding: EdgeInsets.zero, visualDensity: VisualDensity.compact),
                      onPressed: () => _navigateToStats(context),
                      label: const Text('Estatísticas', style: TextStyle(fontSize: 10)),
                      icon: const Icon(Icons.bar_chart, color: Colors.blueGrey, size: 14),
                    ),
                  ],
                ),
              )
          ],
        ),
      ),
    );
  }
}

class _PenduradosColumn extends StatelessWidget {
  final String timeNome;
  final String? escudoUrl;
  final List<Jogador> jogadores;
  final CrossAxisAlignment alignment;

  const _PenduradosColumn({
    required this.timeNome,
    this.escudoUrl,
    required this.jogadores,
    this.alignment = CrossAxisAlignment.center,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch, // Garante que o Center funcione
      children: [
        // ===== ESCUDO E NOME CENTRALIZADOS AQUI =====
        Center(
          child: escudoUrl != null
              ? Image.network(escudoUrl!, width: 40, height: 40, errorBuilder: (c, e, s) => const Icon(Icons.shield_outlined, color: Colors.white, size: 30))
              : const Icon(Icons.shield_outlined, color: Colors.white, size: 30),
        ),
        const SizedBox(height: 4),
        Center(
          child: Text(timeNome, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.white), maxLines: 1, overflow: TextOverflow.ellipsis)
        ),
        const Divider(color: Colors.white54),
        // ===========================================
        Expanded(
          child: ListView.builder(
            itemCount: jogadores.length,
            itemBuilder: (context, index) {
              final jogador = jogadores[index];
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 2.0, horizontal: 2.0),
                child: Row(
                  mainAxisAlignment: (alignment == CrossAxisAlignment.start) ? MainAxisAlignment.start : MainAxisAlignment.end,
                  children: [
                    if (alignment == CrossAxisAlignment.end) ...[
                      Flexible(child: Text(jogador.apelido, style: const TextStyle(fontSize: 12, color: Colors.white), overflow: TextOverflow.ellipsis)),
                      const SizedBox(width: 4),
                      _buildCardIcon(),
                    ],
                    if (alignment == CrossAxisAlignment.start) ...[
                      _buildCardIcon(),
                      const SizedBox(width: 4),
                      Flexible(child: Text(jogador.apelido, style: const TextStyle(fontSize: 12, color: Colors.white), overflow: TextOverflow.ellipsis)),
                    ],
                  ],
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildCardIcon() {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(width: 8, height: 8, decoration: BoxDecoration(color: Colors.yellow[700], shape: BoxShape.circle)),
        const SizedBox(width: 4),
        Container(width: 8, height: 8, decoration: BoxDecoration(color: Colors.yellow[700], shape: BoxShape.circle)),
      ],
    );
  }
}

class _TeamDisplay extends StatelessWidget {
  final String nome;
  final String? escudoUrl;
  final VoidCallback? onTap;

  const _TeamDisplay({required this.nome, this.escudoUrl, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: SizedBox(
        width: 60,
        child: Column(
          children: [
            if (escudoUrl != null && escudoUrl!.isNotEmpty)
              Image.network(
                escudoUrl!,
                height: 40,
                width: 40,
                fit: BoxFit.contain,
                errorBuilder: (context, error, stackTrace) =>
                    const Icon(Icons.shield_outlined, size: 40, color: Colors.grey),
              ),
            const SizedBox(height: 4),
            Text(
              nome,
              textAlign: TextAlign.center,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 10),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }
}