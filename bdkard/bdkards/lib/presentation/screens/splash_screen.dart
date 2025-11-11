import 'dart:async';
import 'package:flutter/material.dart';
import 'home_screen.dart'; // A tela principal para onde vamos navegar

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> with SingleTickerProviderStateMixin {
  // Controladores para as animações
  late AnimationController _logoAnimationController;
  late Animation<double> _logoScaleAnimation;
  double _backgroundOpacity = 0.0; // Para animar o fundo

  @override
  void initState() {
    super.initState();

    // Configuração do AnimationController para a logo (escala)
    _logoAnimationController = AnimationController(
      duration: const Duration(seconds: 2), // Duração da animação da logo
      vsync: this,
    );

    // Animação de escala: começa pequeno (0.7) e vai até o tamanho normal (1.0)
    _logoScaleAnimation = Tween<double>(begin: 0.7, end: 1.0).animate(
      CurvedAnimation(
        parent: _logoAnimationController,
        curve: Curves.easeInOutBack, // Curva de animação para um efeito mais dinâmico
      ),
    );

    // Inicia o processo de animação e navegação
    _startAnimationAndNavigation();
  }

  void _startAnimationAndNavigation() async {
    // 1. Inicia o fade-in do fundo e a animação de escala da logo
    Timer(const Duration(milliseconds: 100), () { // Pequeno atraso antes de começar
      if (mounted) {
        setState(() {
          _backgroundOpacity = 1.0; // Fundo aparece gradualmente
        });
        _logoAnimationController.forward(); // Inicia a animação de escala da logo
      }
    });

    // 2. Agenda a navegação para a tela principal
    Timer(const Duration(seconds: 4), () { // Aumentei o tempo para 4 segundos no total
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (context) => const HomeScreen()),
        );
      }
    });
  }

  @override
  void dispose() {
    _logoAnimationController.dispose(); // Descarta o controlador da animação
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack( // Usamos Stack para empilhar a imagem de fundo e a logo
        children: [
          // IMAGEM DE FUNDO (Estádio) com animação de fade
          AnimatedOpacity(
            opacity: _backgroundOpacity,
            duration: const Duration(seconds: 2), // Duração do fade-in do fundo
            child: SizedBox.expand( // Faz com que a imagem ocupe toda a tela
              child: Image.asset(
                'assets/images/estadio_fundo.jpg',
                fit: BoxFit.cover, // Preenche a tela toda, cortando se necessário
              ),
            ),
          ),
          
          // CONTEÚDO CENTRAL (Logo e Indicador)
          Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // LOGO ANIMADA (escala)
                ScaleTransition( // Aplica a animação de escala
                  scale: _logoScaleAnimation,
                  child: Image.asset(
                    'assets/images/logo.jpg',
                    width: 250, // Tamanho da logo
                  ),
                ),
                const SizedBox(height: 20),
                // INDICADOR DE CARREGAMENTO
                const CircularProgressIndicator(
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}