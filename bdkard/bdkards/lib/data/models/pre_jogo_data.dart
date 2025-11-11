import 'time_estatisticas.dart';

// Modelo para as estatísticas específicas do pré-jogo
class PreJogoEstatisticas {
  final double? mandanteMediaFinalizacoes;
  final double? visitanteMediaFinalizacoes;
  final double? mandanteMediaEscanteios;
  final double? visitanteMediaEscanteios;
  final double? mandanteMediaCartoesAmarelos;
  final double? visitanteMediaCartoesAmarelos;

  PreJogoEstatisticas({
    this.mandanteMediaFinalizacoes,
    this.visitanteMediaFinalizacoes,
    this.mandanteMediaEscanteios,
    this.visitanteMediaEscanteios,
    this.mandanteMediaCartoesAmarelos,
    this.visitanteMediaCartoesAmarelos,
  });
}

// Modelo "pacote" que combina a classificação com as estatísticas do pré-jogo
class PreJogoData {
  final Map<String, TimeEstatisticas> classificacao;
  final PreJogoEstatisticas? preJogoStats;

  PreJogoData({required this.classificacao, this.preJogoStats});
}