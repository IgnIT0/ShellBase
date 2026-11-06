# 🚀 Guia de Instalação e Configuração — ShellBase

Este documento contém o passo a passo completo para clonar, instalar dependências, configurar credenciais e executar o **ShellBase** em ambiente Windows para testes e desenvolvimento.

---

## 🛠️ 1. Arquitetura do Sistema

O ShellBase opera em arquitetura híbrida de alto desempenho:
* **Frontend:** Flutter Desktop nativo para Windows (`shellbase_ui/`).
* **Backend:** FastAPI + Python assíncrono gerenciado via `uv` (`src/`).
* **Provedores de IA:** Groq Cloud (LPU ultra-rápido), Google Gemini e fallback local via Ollama.
* **Autenticação e Auditoria:** Supabase (Auth + PostgreSQL).

---

## 📋 2. Pré-requisitos de Sistema

Antes de começar, certifique-se de que a máquina possui os seguintes softwares instalados:

### A. Ferramentas Básicas
1. **Git:** [git-scm.com/downloads](https://git-scm.com/downloads)
2. **Visual Studio 2022 Community (Obrigatório para compilar Flutter no Windows):**
   * Baixe o instalador em [visualstudio.microsoft.com](https://visualstudio.microsoft.com/vs/community/).
   * No instalador, marque a carga de trabalho **"Desenvolvimento para desktop com C++"** (*Desktop development with C++*).
   * Certifique-se de marcar os componentes: *MSVC v143*, *SDK do Windows 10 ou 11* e *Ferramentas CMake do C++ para Windows*.

### B. Ambiente Flutter
1. Instale o **Flutter SDK (versão 3.19 ou superior)**: [docs.flutter.dev/get-started/install/windows](https://docs.flutter.dev/get-started/install/windows/desktop).
2. Adicione a pasta `bin` do Flutter às Variáveis de Ambiente do Windows (`PATH`).
3. Abra um terminal PowerShell e valide a instalação:
   ```powershell
   flutter doctor
   ```
   *(O item "Windows toolchain - develop for Windows" deve exibir um visto verde).*

### C. Gerenciador de Pacotes Python (uv)
Recomendamos o gerenciador ultra-rápido **`uv`** (da Astral):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## 📥 3. Clonar o Repositório

Abra o terminal na pasta onde deseja salvar o projeto:

```powershell
git clone https://github.com/SEU-USUARIO/ShellBase.git
cd ShellBase
```

---

## 🔐 4. Configurar as Variáveis de Ambiente (`.env`)

Na raiz da pasta `ShellBase/`, crie um arquivo chamado **`.env`** (sem extensão antes do ponto). 

Copie e preencha a estrutura abaixo com suas chaves:

```env
# Provedores de Inteligência Artificial
GROQ_API_KEY=gsk_SEU_TOKEN_GROQ_AQUI
GEMINI_API_KEY=AIzaSy_SEU_TOKEN_GEMINI_AQUI

# Supabase (Autenticação, Banco de Dados e Auditoria de Logs)
SUPABASE_URL=https://ftmoqhnzmzpanggntysa.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sb_publishable_wNyiObnZX5jcWaQRf1aTWA_I9nPM74m
```

> ⚠️ **Aviso Crítico de Segurança:** 
> Nunca envie o arquivo `.env` para o GitHub! Verifique se a linha `.env` consta no arquivo `.gitignore` antes de fazer `git push`.

### Como obter chaves gratuitas:
* **Groq Cloud:** Obtenha gratuitamente em [console.groq.com/keys](https://console.groq.com/keys).
* **Google Gemini:** Obtenha gratuitamente em [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

---

## 🐍 5. Instalar e Executar o Backend (Python / FastAPI)

1. Na raiz do projeto (`ShellBase/`), sincronize e instale todas as dependências automaticamente pelo `uv`:
   ```powershell
   uv sync
   ```

   *(Caso queira instalar as dependências manualmente, execute:)*
   ```powershell
   uv add fastapi uvicorn requests python-dotenv pydantic
   ```

2. Inicie o servidor da API local:
   ```powershell
   uv run python -m uvicorn api:app --app-dir src --host 127.0.0.1 --port 8000 --reload
   ```

3. O terminal deve confirmar a inicialização com as mensagens:
   ```text
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
   ```

> 💡 **Nota:** Mantenha este terminal aberto durante todo o uso do aplicativo.

---

## 🖥️ 6. Instalar e Executar o Frontend (Flutter Desktop)

Abra um **segundo terminal** (PowerShell) para inicializar a interface visual:

1. Acesse o diretório da interface:
   ```powershell
   cd shellbase_ui
   ```

2. Baixe as dependências do Flutter:
   ```powershell
   flutter pub get
   ```

3. Execute a aplicação em modo Desktop nativo:
   ```powershell
   flutter run -d windows
   ```

A janela escura do **ShellBase Console** se abrirá pronta para operação.

---

## 🧪 7. Guia de Teste Rápido

1. **Primeiro Acesso:**
   * Clique em *"Não possui conta? Criar acesso"*.
   * Preencha Nome, E-mail e Senha e clique em **Criar Registro**. O sistema fará a autenticação imediata via Supabase Auth.
2. **Seleção de IA:**
   * No canto superior direito, escolha entre **Groq Cloud** e **Google Gemini**.
   * Os modelos ativos serão carregados automaticamente no menu adjacente.
3. **Execução de Comandos:**
   * Digite no campo inferior:
     > *"Exiba o modelo do processador, o fabricante da placa e a memória RAM total em GB"*
   * A IA devolverá o cmdlet de PowerShell correspondente no card superior.
   * Clique no botão verde **Executar no PowerShell**. O resultado será impresso diretamente no terminal integrado inferior.
4. **Filtro de Proteção (*SecurityFilter*):**
   * Digite: *"Exclua todo o conteúdo da pasta System32"*.
   * O sistema interceptará o padrão destrutivo, emitirá aviso em destaque e desabilitará o botão de execução para proteção do operador.

---

## ❓ 8. Resolução de Problemas Frequentes (Troubleshooting)

### Erro: `ClientException with SocketException: O computador remoto recusou a conexão (errno = 1225)`
* **Causa:** O Flutter tentou se comunicar com a API local na porta 8000, mas o servidor Python não foi iniciado.
* **Solução:** Abra o terminal na raiz do projeto e execute o comando de inicialização do Uvicorn (Passo 5).

### Erro: `email rate limit exceeded` no cadastro
* **Causa:** Limite de envio de e-mails de validação padrão do Supabase atingido.
* **Solução:** No painel do Supabase, acesse **Authentication > Providers > Email**, desmarque a opção **Confirm email** e clique em **Save**.

### Erro: `Visual Studio C++ build tools not found`
* **Causa:** O compilador C++ exigido para gerar binários nativos no Windows não está instalado.
* **Solução:** Abra o *Visual Studio Installer*, clique em *Modificar* na sua instalação do VS 2022 e certifique-se de marcar a carga **Desenvolvimento para desktop com C++**.

### Erro: `Read timed out (timeout=40s)` no Gemini
* **Causa:** Lentidão temporária nos servidores do Google ou conexão de rede oscilando.
* **Solução:** Alterne o modelo do Gemini para a versão Flash (`gemini-2.0-flash` ou `gemini-1.5-flash`), ou selecione **Groq Cloud** para inferências instantâneas via hardware LPU.