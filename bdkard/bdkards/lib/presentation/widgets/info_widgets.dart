import 'package:flutter/material.dart';
import '../../data/models/jogador.dart';

import 'package:flutter/material.dart';
import '../../data/models/jogador.dart';

class InfoHeader extends StatelessWidget {
  final int rodadaAtual;
  const InfoHeader({super.key, required this.rodadaAtual});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      color: Colors.black.withOpacity(0.3),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      // ===== MUDANÇA AQUI: Alinhamento à Esquerda =====
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          RichText(
            text: TextSpan(
              style: const TextStyle(color: Colors.white, fontSize: 22),
              children: [
                const TextSpan(text: 'Rodada atual: ', style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: '$rodadaAtualª'),
              ],
            ),
          ),
        ],
      ),    );
   }
}

class AtletaCard extends StatelessWidget {
  final Jogador jogador;
  const AtletaCard({super.key, required this.jogador});

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white.withOpacity(0.9),
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: Colors.transparent,
          child: (jogador.urlEscudo != null)
              ? Image.network(jogador.urlEscudo!, errorBuilder: (c, e, s) => const Icon(Icons.shield_outlined))
              : const Icon(Icons.shield_outlined),
        ),
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Flexible(child: Text(jogador.apelido, overflow: TextOverflow.ellipsis)),
            if (jogador.estaPendurado) ...[
              const SizedBox(width: 8),
              const Icon(Icons.warning_amber_rounded, color: Colors.orange, size: 16),
            ]
          ],
        ),
        subtitle: Text(jogador.timeNome, style: const TextStyle(fontSize: 12)),
        trailing: AtletaStatus(jogador: jogador),
      ),
    );
  }
}

class AtletaStatus extends StatelessWidget {
  final Jogador jogador;
  const AtletaStatus({super.key, required this.jogador});

  @override
  Widget build(BuildContext context) {
    if (jogador.estaSuspenso) {
      return const Card(color: Colors.red, child: Padding(padding: EdgeInsets.all(4.0), child: Text('SUSPENSO', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 10))));
    }

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          '${jogador.totalAmarelos}',
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        const SizedBox(width: 4),
        Card(
          color: Colors.yellow[700],
          child: const SizedBox(width: 8, height: 12),
        ),
      ],
    );
  }
}

class UltimosJogosWidget extends StatelessWidget {
  final String resultado;
  const UltimosJogosWidget({super.key, required this.resultado});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: resultado.split('').map((r) {
        Color cor;
        String letra;
        if (r == 'V') {
          cor = Colors.green;
          letra = 'V';
        } else if (r == 'E') {
          cor = Colors.grey;
          letra = 'E';
        } else {
          cor = Colors.red;
          letra = 'D';
        }
        return Container(
          margin: const EdgeInsets.symmetric(horizontal: 2),
          width: 20,
          height: 20,
          decoration: BoxDecoration(color: cor, shape: BoxShape.circle),
          child: Center(child: Text(letra, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 10))),
        );
      }).toList(),
    );
  }
}