import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const ShellBaseApp());
}

class ShellBaseApp extends StatelessWidget {
  const ShellBaseApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ShellBase',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF1E1E1E),
        primaryColor: const Color(0xFF0A84FF),
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _promptController = TextEditingController();
  final String _apiUrl = "http://127.0.0.1:8000";

  String _generatedCommand = "Aguardando comando do operador...";
  String _executionOutput = "";
  bool _isLoading = false;
  bool _canExecute = false;
  String? _warningMessage;

  Future<void> _generateCommand() async {
    final prompt = _promptController.text.trim();
    if (prompt.isEmpty) return;

    setState(() {
      _isLoading = true;
      _executionOutput = "";
      _warningMessage = null;
      _generatedCommand = "Processando RAG e IA...";
    });

    try {
      final res = await http.post(
        Uri.parse("$_apiUrl/generate"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"prompt": prompt}),
      );

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        setState(() {
          _generatedCommand = data["command"];
          _canExecute = data["allowed"] ?? false;
          _warningMessage = data["warning"];
        });
      } else {
        setState(() {
          _generatedCommand = "Erro na API: ${res.body}";
          _canExecute = false;
        });
      }
    } catch (e) {
      setState(() {
        _generatedCommand = "Falha ao conectar no backend local: $e";
        _canExecute = false;
      });
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _executeCommand() async {
    setState(() => _isLoading = true);

    try {
      final res = await http.post(
        Uri.parse("$_apiUrl/execute"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "command": _generatedCommand,
          "prompt": _promptController.text.trim(),
        }),
      );

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        setState(() {
          _executionOutput = data["success"]
              ? (data["output"].isEmpty ? "(Sucesso - sem retorno em texto)" : data["output"])
              : "ERRO: ${data["error"]}";
        });
      }
    } catch (e) {
      setState(() => _executionOutput = "Erro ao executar: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'ShellBase Console',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white),
            ),
            const SizedBox(height: 16),

            // Card do Script Gerado
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF2C2C2E),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.white10),
              ),
              child: SelectableText(
                _generatedCommand,
                style: const TextStyle(fontFamily: 'Consolas', color: Color(0xFF64D2FF)),
              ),
            ),

            if (_warningMessage != null) ...[
              const SizedBox(height: 8),
              Text(
                "Atenção: $_warningMessage",
                style: const TextStyle(color: Colors.amberAccent, fontSize: 13),
              ),
            ],

            const SizedBox(height: 12),

            // Botão de Execução
            if (_canExecute)
              ElevatedButton.icon(
                onPressed: _isLoading ? null : _executeCommand,
                icon: const Icon(Icons.play_arrow, color: Colors.white),
                label: const Text('Executar no PowerShell', style: TextStyle(color: Colors.white)),
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF34C759)),
              ),

            const SizedBox(height: 16),

            // Console de Saída
            Expanded(
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF141414),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.white10),
                ),
                child: SingleChildScrollView(
                  child: SelectableText(
                    _executionOutput.isEmpty ? "> Terminal ocioso..." : _executionOutput,
                    style: const TextStyle(fontFamily: 'Consolas', color: Colors.greenAccent),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Input inferior
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _promptController,
                    onSubmitted: (_) => _generateCommand(),
                    decoration: InputDecoration(
                      hintText: 'Digite o comando em linguagem natural...',
                      filled: true,
                      fillColor: const Color(0xFF2C2C2E),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: BorderSide.none,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                ElevatedButton(
                  onPressed: _isLoading ? null : _generateCommand,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF0A84FF),
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  child: _isLoading
                      ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : const Text('Enviar', style: TextStyle(color: Colors.white)),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}