// lib/data/models/escalacao.dart

class JogoEscalacao {
  final TimeEscalacao mandante;
  final TimeEscalacao visitante;

  JogoEscalacao({required this.mandante, required this.visitante});
}

class TimeEscalacao {
  final String nome;
  final String formacao;
  final List<JogadorTitular> titulares;
  final List<JogadorReserva> reservas;
  final List<JogadorAusente> foraDeJogo;

  TimeEscalacao({
    required this.nome,
    required this.formacao,
    required this.titulares,
    required this.reservas,
    required this.foraDeJogo,
  });
}

class JogadorTitular {
  final String nome;
  final String numero;
  final String fotoUrl;
  final double posX;
  final double posY;

  JogadorTitular({
    required this.nome,
    required this.numero,
    required this.fotoUrl,
    required this.posX,
    required this.posY,
  });

  factory JogadorTitular.fromJson(Map<String, dynamic> json) {
    return JogadorTitular(
      nome: json['nome_jogador'] as String? ?? 'N/A',
      numero: json['numero_camisa'] as String? ?? 'S/N',
      fotoUrl: json['foto_url'] as String? ?? '',
      posX: (json['pos_x'] as num?)?.toDouble() ?? 50.0,
      posY: (json['pos_y'] as num?)?.toDouble() ?? 50.0,
    );
  }
}

class JogadorReserva {
  final String nome;
  final String numero;
  final String posicao;
  final String fotoUrl;

  JogadorReserva({
    required this.nome,
    required this.numero,
    required this.posicao,
    required this.fotoUrl,
  });

  factory JogadorReserva.fromJson(Map<String, dynamic> json) {
    return JogadorReserva(
      nome: json['nome_jogador'] as String? ?? 'N/A',
      numero: json['numero_camisa'] as String? ?? 'S/N',
      posicao: json['posicao'] as String? ?? 'N/A',
      fotoUrl: json['foto_url'] as String? ?? '',
    );
  }
}

class JogadorAusente {
  final String nome;
  final String posicao;
  final String motivo;
  final String fotoUrl;

  JogadorAusente({
    required this.nome,
    required this.posicao,
    required this.motivo,
    required this.fotoUrl,
  });

  // >>> MÉTODO CORRIGIDO E ROBUSTO <<<
 factory JogadorAusente.fromJson(Map<String, dynamic> json) {
        // A string original pode ser algo como "Zagueiro Central (Lesionado)" ou apenas "Suspenso"
        final String originalInfo = json['posicao'] as String? ?? 'Indisponível';
        
        String posicaoReal = 'N/A'; // Padrão: Posição não informada
        String motivoFinal = originalInfo; // Padrão: A informação inteira é o motivo

        // 1. Tenta separar se houver parênteses
        if (originalInfo.contains('(') && originalInfo.contains(')')) {
            final parts = originalInfo.split('(');
            
            if (parts.length == 2) {
                // A primeira parte (parts[0]) DEVE ser a posição.
                String potencialPosicao = parts[0].trim();

                // 2. Verifica se a posição é um termo genérico de ausência e ignora
                if (potencialPosicao.toLowerCase().contains('ausente') || potencialPosicao.isEmpty) {
                     posicaoReal = 'N/A'; // Mantém o padrão
                } else {
                     posicaoReal = potencialPosicao; // Usa a posição real (ex: "Zagueiro")
                }
                
                // Extrai o motivo
                motivoFinal = parts[1].replaceAll(')', '').trim();
            }
        }
        
        // Se após a tentativa de extração, motivoFinal ainda for igual a originalInfo,
        // significa que não houve parênteses, então o motivoFinal já está correto.

        return JogadorAusente(
            nome: json['nome_jogador'] as String? ?? 'N/A',
            posicao: posicaoReal,   // << Deve ser 'N/A' ou 'Atacante'
            motivo: motivoFinal,    // << Deve ser 'Lesionado' ou 'Suspenso'
            fotoUrl: json['foto_url'] as String? ?? '',
        );
    }
}