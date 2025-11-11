class Jogo {
  final int id; // <-- 1. ADICIONE ESTA LINHA
  final int rodada;
  final String? data;
  final String? hora;
  final String? local;
  final String? mandanteNome;
  final String? mandanteEscudo;
  final String? mandanteGols;
  final String? visitanteNome;
  final String? visitanteEscudo;
  final String? visitanteGols;

  Jogo({
    required this.id, // <-- 2. ADICIONE ESTA LINHA
    required this.rodada,
    this.data,
    this.hora,
    this.local,
    this.mandanteNome,
    this.mandanteEscudo,
    this.mandanteGols,
    this.visitanteNome,
    this.visitanteEscudo,
    this.visitanteGols,
  });
}