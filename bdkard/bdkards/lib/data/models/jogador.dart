class Jogador {
  final String apelido;
  final String timeNome;
  final String? urlEscudo;
  final int totalAmarelos;
  final int totalVermelhos;
  final int rodadaUltimoVermelho;
  final int rodadaAtual;
  final int rodadaSuspensaoAmarelo; // <-- NOVO CAMPO ADICIONADO

  Jogador({
    required this.apelido,
    required this.timeNome,
    this.urlEscudo,
    required this.totalAmarelos,
    required this.totalVermelhos,
    required this.rodadaUltimoVermelho,
    required this.rodadaAtual,
    required this.rodadaSuspensaoAmarelo, // <-- NOVO CAMPO ADICIONADO
  });

  // Lógica de suspensão aprimorada
  bool get estaSuspenso {
    // Suspenso se recebeu vermelho na última rodada finalizada
    if (rodadaUltimoVermelho == rodadaAtual) {
      return true;
    }
    // Suspenso se completou um ciclo de 3 amarelos na última rodada finalizada
    if (rodadaSuspensaoAmarelo == rodadaAtual) {
      return true;
    }
    return false;
  }

  bool get estaPendurado {
    // Continua pendurado se tiver 2, 5, 8, etc., cartões.
    return totalAmarelos > 0 && totalAmarelos % 3 == 2;
  }
}