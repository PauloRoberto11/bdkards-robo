import 'package:flutter/material.dart';
import 'atletas_screen.dart';
import 'classificacao_screen.dart';
import 'jogos_screen.dart';

class BottomNavigationScreen extends StatefulWidget {
  const BottomNavigationScreen({super.key});

  @override
  State<BottomNavigationScreen> createState() => _BottomNavigationScreenState();
}

class _BottomNavigationScreenState extends State<BottomNavigationScreen> {
  int _selectedIndex = 0; // O índice da aba selecionada (começa na aba 'Jogos')

  // A lista de todas as nossas telas principais
  static const List<Widget> _widgetOptions = <Widget>[
    JogosScreen(),
    AtletasScreen(),
    ClassificacaoScreen(),
  ];

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // O corpo da tela será a tela selecionada da nossa lista
      body: Center(
        child: _widgetOptions.elementAt(_selectedIndex),
      ),
      // A barra de navegação na parte inferior
      bottomNavigationBar: BottomNavigationBar(
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
            icon: Icon(Icons.bar_chart),
            label: 'Classificação',
          ),
        ],
        currentIndex: _selectedIndex,
        selectedItemColor: Colors.green[800],
        onTap: _onItemTapped,
        backgroundColor: Colors.white.withOpacity(0.9), // Fundo semi-transparente
      ),
    );
  }
}