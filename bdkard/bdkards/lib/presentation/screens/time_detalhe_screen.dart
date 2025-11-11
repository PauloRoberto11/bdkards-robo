import 'package:flutter/material.dart';
import '../../data/database/database_helper.dart';
import '../../data/models/jogador.dart';

class TimeDetalheScreen extends StatelessWidget {
  final String timeNome;
  const TimeDetalheScreen({super.key, required this.timeNome});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(timeNome),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
      ),
      body: FutureBuilder<List<Jogador>>(
        future: DatabaseHelper.instance.getJogadoresPorTime(timeNome),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Erro ao carregar jogadores: ${snapshot.error}', style: const TextStyle(color: Colors.white)));
          }
          if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return const Center(child: Text('Nenhum jogador com cartões encontrado para este time.', style: TextStyle(color: Colors.white)));
          }

          final jogadores = snapshot.data!;
          final escudoUrl = jogadores.isNotEmpty ? jogadores.first.urlEscudo : null;

          return Column(
            children: [
              _TimeHeader(timeNome: timeNome, escudoUrl: escudoUrl),
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('JOGADOR', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white70)),
                    Text('CARTÕES', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white70)),
                  ],
                ),
              ),
              const Divider(height: 1, color: Colors.white24),
              Expanded(
                child: ListView.separated(
                  itemCount: jogadores.length,
                  itemBuilder: (context, index) {
                    return _JogadorInfo(jogador: jogadores[index]);
                  },
                  separatorBuilder: (context, index) => const Divider(height: 1, color: Colors.white24),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _TimeHeader extends StatelessWidget {
  final String timeNome;
  final String? escudoUrl;

  const _TimeHeader({required this.timeNome, this.escudoUrl});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      color: Colors.black.withOpacity(0.3),
      child: Row(
        children: [
          if (escudoUrl != null)
            Image.network(
              escudoUrl!,
              height: 40,
              width: 40,
              errorBuilder: (c, e, s) => const Icon(Icons.shield_outlined, size: 40, color: Colors.white),
            )
          else
            const Icon(Icons.shield_outlined, size: 40, color: Colors.white),
          const SizedBox(width: 16),
          Expanded(
            child: Text(
              timeNome,
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white),
            ),
          ),
        ],
      ),
    );
  }
}

class _JogadorInfo extends StatelessWidget {
  final Jogador jogador;
  const _JogadorInfo({required this.jogador});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      title: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Flexible(child: Text(jogador.apelido, style: const TextStyle(color: Colors.white), overflow: TextOverflow.ellipsis)),
          if (jogador.estaPendurado) ...[
            const SizedBox(width: 8),
            const Icon(Icons.warning_amber_rounded, color: Colors.orange, size: 16),
          ]
        ],
      ),
      trailing: _CardStatus(jogador: jogador),
    );
  }
}

class _CardStatus extends StatelessWidget {
  final Jogador jogador;
  const _CardStatus({required this.jogador});

  @override
  Widget build(BuildContext context) {
    if (jogador.estaSuspenso) {
      return const Card(
        color: Colors.red,
        child: Padding(
          padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          child: Text('SUSPENSO', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 10)),
        ),
      );
    }

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          '${jogador.totalAmarelos}',
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white),
        ),
        const SizedBox(width: 4),
        Card(
          color: Colors.yellow[700],
          child: const SizedBox(width: 8, height: 12),
        ),
        const SizedBox(width: 8),
        Text(
          '${jogador.totalVermelhos}',
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white),
        ),
        const SizedBox(width: 4),
        const Card(
          color: Colors.red,
          child: SizedBox(width: 8, height: 12),
        ),
      ],
    );
  }
}