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
      home: const AuthGate(),
    );
  }
}

class AuthGate extends StatefulWidget {
  const AuthGate({super.key});

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  Map<String, dynamic>? _currentUser;

  void _onLoginSuccess(Map<String, dynamic> user) {
    setState(() => _currentUser = user);
  }

  void _onLogout() {
    setState(() => _currentUser = null);
  }

  @override
  Widget build(BuildContext context) {
    if (_currentUser == null) {
      return AuthScreen(onLoginSuccess: _onLoginSuccess);
    }
    return HomeScreen(
      user: _currentUser!,
      onLogout: _onLogout,
    );
  }
}

// ================= TELA DE AUTENTICAÇÃO =================
class AuthScreen extends StatefulWidget {
  final Function(Map<String, dynamic>) onLoginSuccess;

  const AuthScreen({super.key, required this.onLoginSuccess});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _nameController = TextEditingController();
  
  bool _isRegister = false;
  bool _isLoading = false;
  String? _errorMessage;

  final String _apiUrl = "http://127.0.0.1:8000";

  Future<void> _submit() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text.trim();
    final name = _nameController.text.trim();

    if (email.isEmpty || password.isEmpty || (_isRegister && name.isEmpty)) {
      setState(() => _errorMessage = "Preencha todos os campos.");
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final endpoint = _isRegister ? "$_apiUrl/auth/register" : "$_apiUrl/auth/login";
      final body = _isRegister
          ? {"name": name, "email": email, "password": password}
          : {"email": email, "password": password};

      final res = await http.post(
        Uri.parse(endpoint),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(body),
      );

      final data = jsonDecode(res.body);

      if (res.statusCode == 200 && data["success"] == true) {
        if (data["user"] != null) {
          widget.onLoginSuccess(Map<String, dynamic>.from(data["user"]));
        } else {
          setState(() => _errorMessage = "Cadastro realizado, mas a sessão não foi retornada.");
        }
      } else {
        setState(() => _errorMessage = data["detail"] ?? "Falha na autenticação.");
      }
    } catch (e) {
      setState(() => _errorMessage = "Erro ao conectar à API local (127.0.0.1:8000): $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Container(
          width: 420,
          padding: const EdgeInsets.all(32),
          decoration: BoxDecoration(
            color: const Color(0xFF2C2C2E),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: Colors.white10),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'ShellBase Access',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white),
              ),
              const SizedBox(height: 6),
              Text(
                _isRegister ? 'Cadastre seu acesso de operador' : 'Faça login para desbloquear o console',
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 13, color: Colors.white54),
              ),
              const SizedBox(height: 24),

              if (_isRegister) ...[
                TextField(
                  controller: _nameController,
                  decoration: const InputDecoration(
                    labelText: 'Nome Completo',
                    filled: true,
                    fillColor: Color(0xFF1E1E1E),
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
              ],

              TextField(
                controller: _emailController,
                decoration: const InputDecoration(
                  labelText: 'E-mail do operador',
                  filled: true,
                  fillColor: Color(0xFF1E1E1E),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),

              TextField(
                controller: _passwordController,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'Senha',
                  filled: true,
                  fillColor: Color(0xFF1E1E1E),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),

              if (_errorMessage != null) ...[
                Text(
                  _errorMessage!,
                  style: const TextStyle(color: Colors.redAccent, fontSize: 13),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 12),
              ],

              ElevatedButton(
                onPressed: _isLoading ? null : _submit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF0A84FF),
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
                child: _isLoading
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : Text(_isRegister ? 'Criar Registro' : 'Entrar no Sistema', style: const TextStyle(color: Colors.white, fontSize: 15)),
              ),
              const SizedBox(height: 16),

              TextButton(
                onPressed: () {
                  setState(() {
                    _isRegister = !_isRegister;
                    _errorMessage = null;
                  });
                },
                child: Text(
                  _isRegister ? 'Já possui login? Entrar' : 'Não possui conta? Criar acesso',
                  style: const TextStyle(color: Color(0xFF64D2FF)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ================= TELA PRINCIPAL DO CONSOLE =================
class HomeScreen extends StatefulWidget {
  final Map<String, dynamic> user;
  final VoidCallback onLogout;

  const HomeScreen({super.key, required this.user, required this.onLogout});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _promptController = TextEditingController();
  final String _apiUrl = "http://127.0.0.1:8000";

  String _selectedProvider = "groq";
  String _selectedModel = "llama-3.3-70b-versatile";
  String _generatedCommand = "Aguardando comando do operador...";
  String _executionOutput = "";
  bool _isLoading = false;
  bool _canExecute = false;
  String? _warningMessage;

  // Mapa dinâmico preenchido pela API
  Map<String, List<String>> _providerModels = {
    "groq": ["llama-3.3-70b-versatile"],
    "gemini": ["gemini-2.0-flash"],
    "ollama": ["qwen2.5-coder:7b"],
  };

  @override
  void initState() {
    super.initState();
    _fetchLiveProviders();
  }

  Future<void> _fetchLiveProviders() async {
    try {
      final res = await http.get(Uri.parse("$_apiUrl/providers"));
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        final List providers = data["providers"] ?? [];
        final Map<String, List<String>> newMap = {};

        for (var p in providers) {
          final id = p["id"] as String;
          final List models = p["models"] ?? [];
          newMap[id] = models.map((e) => e.toString()).toList();
        }

        if (newMap.isNotEmpty && mounted) {
          setState(() {
            _providerModels = newMap;
            if (_providerModels[_selectedProvider]?.isNotEmpty ?? false) {
              _selectedModel = _providerModels[_selectedProvider]!.first;
            }
          });
        }
      }
    } catch (e) {
      debugPrint("Falha ao atualizar lista dinâmica de modelos: $e");
    }
  }

  Future<void> _generateCommand() async {
    final prompt = _promptController.text.trim();
    if (prompt.isEmpty) return;

    setState(() {
      _isLoading = true;
      _executionOutput = "";
      _warningMessage = null;
      _generatedCommand = "Consultando IA (${_selectedProvider.toUpperCase()} - $_selectedModel)...";
    });

    try {
      final res = await http.post(
        Uri.parse("$_apiUrl/generate"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "prompt": prompt,
          "provider": _selectedProvider,
          "model": _selectedModel,
        }),
      );

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        setState(() {
          _generatedCommand = data["command"];
          _canExecute = data["allowed"] ?? false;
          _warningMessage = data["warning"];
        });
      } else {
        final err = jsonDecode(res.body);
        setState(() {
          _generatedCommand = "Erro na API: ${err['detail'] ?? res.body}";
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
          "user_email": widget.user["email"],
          "user_name": widget.user["name"],
        }),
      );

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        setState(() {
          _executionOutput = data["success"]
              ? (data["output"].isEmpty ? "(Comando executado com sucesso - sem retorno de texto)" : data["output"])
              : "ERRO DE EXECUÇÃO:\n${data["error"]}";
        });
      }
    } catch (e) {
      setState(() => _executionOutput = "Erro ao disparar comando: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final userName = widget.user["name"] ?? "Operador";
    final userEmail = widget.user["email"] ?? "";
    final currentModels = _providerModels[_selectedProvider] ?? [];

    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Top Bar
            Row(
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'ShellBase Console',
                      style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                    Text(
                      'Operador ativo: $userName ($userEmail)',
                      style: const TextStyle(fontSize: 12, color: Colors.white54),
                    ),
                  ],
                ),
                const Spacer(),

                // Status de Chave do .env
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: Colors.green.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: Colors.green.withValues(alpha: 0.4)),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.auto_awesome, size: 14, color: Colors.greenAccent),
                      SizedBox(width: 6),
                      Text("Catálogo Dinâmico Ativo", style: TextStyle(fontSize: 12, color: Colors.greenAccent)),
                    ],
                  ),
                ),
                const SizedBox(width: 12),

                // Seletor de Provedor
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  decoration: BoxDecoration(
                    color: const Color(0xFF2C2C2E),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.white12),
                  ),
                  child: DropdownButtonHideUnderline(
                    child: DropdownButton<String>(
                      value: _selectedProvider,
                      dropdownColor: const Color(0xFF2C2C2E),
                      items: const [
                        DropdownMenuItem(value: "groq", child: Text("Groq Cloud")),
                        DropdownMenuItem(value: "gemini", child: Text("Google Gemini")),
                        DropdownMenuItem(value: "ollama", child: Text("Ollama Local")),
                      ],
                      onChanged: (val) {
                        if (val != null) {
                          setState(() {
                            _selectedProvider = val;
                            final list = _providerModels[val] ?? [];
                            _selectedModel = list.isNotEmpty ? list.first : "";
                          });
                        }
                      },
                    ),
                  ),
                ),
                const SizedBox(width: 8),

                // Seletor de Modelo Dinâmico
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  decoration: BoxDecoration(
                    color: const Color(0xFF2C2C2E),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.white12),
                  ),
                  child: DropdownButtonHideUnderline(
                    child: DropdownButton<String>(
                      value: currentModels.contains(_selectedModel)
                          ? _selectedModel
                          : (currentModels.isNotEmpty ? currentModels.first : null),
                      dropdownColor: const Color(0xFF2C2C2E),
                      items: currentModels.map((m) {
                        return DropdownMenuItem(value: m, child: Text(m));
                      }).toList(),
                      onChanged: (val) {
                        if (val != null) setState(() => _selectedModel = val);
                      },
                    ),
                  ),
                ),
                const SizedBox(width: 8),

                IconButton(
                  tooltip: 'Desconectar da Sessão',
                  icon: const Icon(Icons.logout, color: Colors.redAccent),
                  onPressed: widget.onLogout,
                ),
              ],
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

            if (_canExecute)
              ElevatedButton.icon(
                onPressed: _isLoading ? null : _executeCommand,
                icon: const Icon(Icons.play_arrow, color: Colors.white),
                label: const Text('Executar no PowerShell', style: TextStyle(color: Colors.white)),
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF34C759)),
              ),

            const SizedBox(height: 16),

            // Terminal
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
                    _executionOutput.isEmpty ? "> Terminal aguardando despacho..." : _executionOutput,
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