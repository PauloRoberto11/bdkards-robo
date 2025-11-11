// lib/main.dart

import 'dart:io';
import 'package:flutter/material.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:window_manager/window_manager.dart'; 
import 'presentation/screens/splash_screen.dart'; // <<< VERIFIQUE SE ESTE CAMINHO ESTÁ CORRETO
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  if (Platform.isWindows || Platform.isLinux || Platform.isMacOS) {
    // 1. Configuração do SQFlite
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;

    // 2. Configuração do Gerenciador de Janelas (Window Manager)
    await windowManager.ensureInitialized();

    // Definindo o tamanho alvo (que será o tamanho inicial e máximo)
    const Size initialMaxSize = Size(800.0, 742.0); 

    // Configurações para a janela desktop
    WindowOptions windowOptions = const WindowOptions(
      size: initialMaxSize, 
      minimumSize: Size(300.0, 700.0), 
      maximumSize: initialMaxSize, 
      center: true,
      skipTaskbar: false,
      titleBarStyle: TitleBarStyle.normal,
    );

    // Aplica as configurações na janela antes de ela ser exibida
    windowManager.waitUntilReadyToShow(windowOptions, () async {
      await windowManager.show();
      await windowManager.focus();
    });
  }

  bool dbOk = await _checkForDatabaseUpdate();

  runApp(MyApp(databaseReady: dbOk));
}

Future<bool> _checkForDatabaseUpdate() async {
  print("Verificando atualizações do banco de dados...");
  try {
    final url = Uri.parse('https://raw.githubusercontent.com/PauloRoberto11/bdkards-robo/main/database/brasileirao.db');

    // Usando path_provider para encontrar a pasta de documentos correta
    final Directory documentsDirectory = await getApplicationDocumentsDirectory();
    final String dbPath = p.join(documentsDirectory.path, 'brasileirao.db');
    final File localDbFile = File(dbPath);

    print("Tentando baixar o banco de dados para: $dbPath");
    final response = await http.get(url).timeout(const Duration(seconds: 20));

    if (response.statusCode == 200) {
      if (!await localDbFile.parent.exists()) {
        await localDbFile.parent.create(recursive: true);
      }
      await localDbFile.writeAsBytes(response.bodyBytes);
      print("✅ Banco de dados baixado com sucesso!");
      return true;
    } else {
      print("❌ Erro ao baixar o banco de dados: Status ${response.statusCode}");
      if (await localDbFile.exists()) {
        print("    > Usando a versão local existente do banco de dados.");
        return true;
      }
      return false;
    }
  } catch (e) {
    print("❌ Falha na verificação de atualização: $e");
    final Directory documentsDirectory = await getApplicationDocumentsDirectory();
    final String dbPath = p.join(documentsDirectory.path, 'brasileirao.db');
    final File localDbFile = File(dbPath);
    if (await localDbFile.exists()) {
      print("    > Usando a versão local existente do banco de dados.");
      return true;
    }
    return false;
  }
}

class MyApp extends StatelessWidget {
  final bool databaseReady;
  const MyApp({super.key, required this.databaseReady});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        image: DecorationImage(
          image: AssetImage("assets/images/bk_app.jpg"),
          fit: BoxFit.cover,
        ),
      ),
      child: MaterialApp(
        title: 'Bdkards Brasileirão',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          primarySwatch: Colors.green,
          scaffoldBackgroundColor: Colors.transparent,
          appBarTheme: const AppBarTheme(
            backgroundColor: Colors.green,
            foregroundColor: Colors.white,
          ),
        ),
        home: databaseReady ? const SplashScreen() : const DatabaseErrorScreen(),
      ),
    );
  }
}

class DatabaseErrorScreen extends StatelessWidget {
  const DatabaseErrorScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1E2A3A),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, color: Colors.red, size: 60),
              const SizedBox(height: 20),
              const Text(
                'Falha ao Carregar Dados',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                'Não foi possível baixar o arquivo de dados do campeonato (brasileirao.db).\n\nVerifique sua conexão com a internet e reinicie o aplicativo.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey[300], fontSize: 16),
              ),
            ],
          ),
        ),
      ),
    );
  }
}