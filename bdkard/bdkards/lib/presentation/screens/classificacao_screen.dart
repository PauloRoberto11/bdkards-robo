import 'package:flutter/material.dart';
import '../../data/database/database_helper.dart';
import '../../data/models/classificacao_time.dart';
import '../widgets/info_widgets.dart';

class ClassificacaoScreen extends StatelessWidget {
  const ClassificacaoScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Classificação'),
        centerTitle: true,
      ),
      // ===== MUDANÇA AQUI: Adicionado Container para a opacidade =====
      body: Container(
        color: Colors.black.withOpacity(0.5),
        child: FutureBuilder<List<ClassificacaoTime>>(
          future: DatabaseHelper.instance.getTabelaClassificacao(),
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return Center(child: Text('Erro: ${snapshot.error}', style: const TextStyle(color: Colors.white)));
            }
            if (!snapshot.hasData || snapshot.data!.isEmpty) {
              return const Center(child: Text('Nenhuma classificação encontrada.', style: TextStyle(color: Colors.white)));
            }

            final classificacao = snapshot.data!;

            return Scrollbar(
              thumbVisibility: true,
              child: SingleChildScrollView(
                child: SizedBox(
                  width: double.infinity,
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: _buildDataTable(classificacao),
                  ),
                ),
              ),
            );
          },
        ),
      ),
      // ===============================================================
    );
  }

  Widget _buildDataTable(List<ClassificacaoTime> classificacao) {
    const textStyle = TextStyle(color: Colors.white, fontWeight: FontWeight.bold);
    const cellTextStyle = TextStyle(color: Colors.white);

    return DataTable(
      columnSpacing: 20,
      columns: const [
        DataColumn(label: Text('Pos', style: textStyle)),
        DataColumn(label: Text('Time', style: textStyle)),
        DataColumn(label: Text('P', style: textStyle)),
        DataColumn(label: Text('Últ. Jogos', style: textStyle)),
      ],
      rows: classificacao.map((time) {
        return DataRow(
          cells: [
            DataCell(Center(child: Text(time.posicao?.toString() ?? '-', style: cellTextStyle))),
            DataCell(
              Row(
                children: [
                  if (time.urlEscudo != null)
                    Image.network(time.urlEscudo!, width: 24, height: 24, errorBuilder: (c, e, s) => const Icon(Icons.shield_outlined, color: Colors.white)),
                  const SizedBox(width: 8),
                  Text(time.nome, style: cellTextStyle),
                ],
              ),
            ),
            DataCell(Center(child: Text(time.pontos?.toString() ?? '-', style: cellTextStyle))),
            DataCell(UltimosJogosWidget(resultado: time.ultimosJogos ?? '')),
          ],
        );
      }).toList(),
    );
  }
}