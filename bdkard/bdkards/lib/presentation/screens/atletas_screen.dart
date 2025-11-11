import 'package:flutter/material.dart';
import '../../data/database/database_helper.dart';
import '../../data/models/campeonato_data.dart';
import '../../data/models/time.dart';
import '../widgets/info_widgets.dart';
import 'time_detalhe_screen.dart';

class AtletasScreen extends StatelessWidget {
  const AtletasScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('ATLETAS'),
          centerTitle: true,
          bottom: TabBar(
            labelColor: Colors.white,
            unselectedLabelColor: Colors.grey[300],
            indicatorColor: Colors.white,
            tabs: const [
              Tab(text: 'GERAL'),
              Tab(text: 'TIMES'),
            ],
          ),
        ),
        body: const TabBarView(
          children: [
            _buildGeralTab(),
            _buildTimesTab(),
          ],
        ),
      ),
    );
  }
}

class _buildGeralTab extends StatelessWidget {
  const _buildGeralTab();

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<CampeonatoData>(
      future: DatabaseHelper.instance.getCampeonatoData(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Center(child: Text('Erro: ${snapshot.error}', style: const TextStyle(color: Colors.white)));
        }
        if (!snapshot.hasData || snapshot.data!.jogadores.isEmpty) {
          return const Center(child: Text('Nenhum atleta com cartões.', style: TextStyle(color: Colors.white)));
        }
        final campeonatoData = snapshot.data!;
        return Column(
          children: [
            InfoHeader(rodadaAtual: campeonatoData.rodadaAtual),
            Expanded(
              child: ListView.builder(
                itemCount: campeonatoData.jogadores.length,
                itemBuilder: (context, index) {
                  return AtletaCard(jogador: campeonatoData.jogadores[index]);
                },
              ),
            ),
          ],
        );
      },
    );
  }
}

class _buildTimesTab extends StatelessWidget {
  const _buildTimesTab();

  void _navigateToTeamDetail(BuildContext context, String timeNome) {
    Navigator.push(context, MaterialPageRoute(builder: (context) => TimeDetalheScreen(timeNome: timeNome)));
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<Time>>(
      future: DatabaseHelper.instance.getTodosOsTimes(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Center(child: Text('Erro: ${snapshot.error}', style: const TextStyle(color: Colors.white)));
        }
        if (!snapshot.hasData || snapshot.data!.isEmpty) {
          return const Center(child: Text('Nenhum time encontrado.', style: const TextStyle(color: Colors.white)));
        }
        final times = snapshot.data!;
        
        // ===== MUDANÇA AQUI: Adicionado LayoutBuilder para responsividade =====
        return LayoutBuilder(
          builder: (context, constraints) {
            final bool isNarrow = constraints.maxWidth < 450;
            final int crossAxisCount = isNarrow ? 4 : 5;

            return GridView.builder(
              padding: const EdgeInsets.all(8.0),
              gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: crossAxisCount,
                crossAxisSpacing: 8,
                mainAxisSpacing: 8,
                childAspectRatio: 0.9,
              ),
              itemCount: times.length,
              itemBuilder: (context, index) {
                return _TeamGridItem(
                  time: times[index],
                  onTap: () => _navigateToTeamDetail(context, times[index].nome),
                );
              },
            );
          },
        );
        // ====================================================================
      },
    );
  }
}

class _TeamGridItem extends StatelessWidget {
  final Time time;
  final VoidCallback onTap;
  const _TeamGridItem({required this.time, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Card(
        color: Colors.white.withOpacity(0.1),
        elevation: 0,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Expanded(
              flex: 3,
              child: Center(
                child: SizedBox(
                  width: 50,
                  height: 50,
                  child: time.urlEscudo != null
                      ? Image.network(time.urlEscudo!, fit: BoxFit.contain, errorBuilder: (c, e, s) => const Icon(Icons.shield_outlined, color: Colors.white, size: 40))
                      : const Icon(Icons.shield_outlined, color: Colors.white, size: 40),
                ),
              ),
            ),
            Expanded(
              flex: 2,
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 2.0),
                  child: Text(
                    time.nome,
                    textAlign: TextAlign.center,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}