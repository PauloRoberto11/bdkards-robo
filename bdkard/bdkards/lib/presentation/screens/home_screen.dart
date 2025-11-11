import 'package:flutter/material.dart';
import 'atletas_screen.dart';
import 'jogos_screen.dart';
import 'classificacao_screen.dart'; // Importa a nova tela

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;

  // ORDEM ATUALIZADA: Jogos, Atletas, Classificação
  static const List<Widget> _screens = <Widget>[
    JogosScreen(),
    AtletasScreen(),
    ClassificacaoScreen(), // Adiciona a nova tela
  ];

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: _screens.elementAt(_selectedIndex),
      ),
      bottomNavigationBar: BottomNavigationBar(
        // ITENS ATUALIZADOS
        items: const <BottomNavigationBarItem>[
          BottomNavigationBarItem(
            icon: Icon(Icons.sports_soccer),
            label: 'Jogos',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person),
            label: 'Atletas',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.leaderboard), // Ícone para a tabela
            label: 'Classificação',
          ),
        ],
        currentIndex: _selectedIndex,
        selectedItemColor: Colors.green[800],
        onTap: _onItemTapped,
      ),
    );
  }
}