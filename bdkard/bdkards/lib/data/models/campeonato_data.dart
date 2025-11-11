import 'jogador.dart';

class CampeonatoData {
  final List<Jogador> jogadores;
  final int rodadaAtual; // Renomeado para maior clareza

  CampeonatoData({
    required this.jogadores,
    required this.rodadaAtual,
  });
}