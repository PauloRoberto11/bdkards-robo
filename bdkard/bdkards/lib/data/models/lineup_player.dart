class LineupData {
  final List<LineupPlayer> homeTeam;
  final List<LineupPlayer> awayTeam;
  final String homeFormation;
  final String awayFormation;

  LineupData({
    required this.homeTeam,
    required this.awayTeam,
    required this.homeFormation,
    required this.awayFormation,
  });
}

class LineupPlayer {
  final String name;
  final String number;
  final String imageUrl;
  final double leftPercent; // Posição X (horizontal) em porcentagem
  final double bottomPercent; // Posição Y (vertical) em porcentagem

  LineupPlayer({
    required this.name,
    required this.number,
    required this.imageUrl,
    required this.leftPercent,
    required this.bottomPercent,
  });
}