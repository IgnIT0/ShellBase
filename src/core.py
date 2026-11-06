import os
import re
import requests
import subprocess
import time
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ExecutionResult:
    command: str
    output: str
    error: str
    duration_ms: int
    success: bool

class SecurityFilter:
    BLOCKLIST = [
        r"format\s+[a-z]:",
        r"remove-item\s+.*system32",
        r"stop-computer",
        r"restart-computer",
        r"rmdir\s+/s\s+/q\s+c:",
    ]

    @classmethod
    def analyze(cls, command: str) -> tuple[bool, Optional[str]]:
        cmd_lower = command.lower()
        for pattern in cls.BLOCKLIST:
            if re.search(pattern, cmd_lower):
                return False, f"Comando bloqueado por regra de segurança crítica: {pattern}"
        if "remove-item" in cmd_lower or "drop" in cmd_lower:
            return True, "Comando com potencial destrutivo. Revise atentamente antes de executar."
        return True, None

class ShellBaseEngine:
    PROVIDERS: Dict[str, Dict[str, Any]] = {
        "groq": {
            "name": "Groq Cloud (Ultra-rápido)",
            "url": "https://api.groq.com/openai/v1/chat/completions",
            "models_url": "https://api.groq.com/openai/v1/models",
            "default_model": "llama-3.3-70b-versatile",
            "fallback_models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "qwen-2.5-coder-32b"],
        },
        "gemini": {
            "name": "Google Gemini",
            "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            "models_url": "https://generativelanguage.googleapis.com/v1beta/models",
            "default_model": "gemini-2.0-flash",
            "fallback_models": ["gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro-latest"],
        },
        "ollama": {
            "name": "Ollama Local (Offline)",
            "url": "http://127.0.0.1:11434/v1/chat/completions",
            "models_url": "http://127.0.0.1:11434/api/tags",
            "default_model": "qwen2.5-coder:7b",
            "fallback_models": ["qwen2.5-coder:7b"],
        },
    }

    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL", "")
        self.supabase_key = (
            supabase_key 
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") 
            or os.getenv("SUPABASE_KEY", "")
        )
        self._model_cache: Dict[str, List[str]] = {}

    def fetch_live_models(self, provider: str) -> List[str]:
        """Consulta as APIs dos provedores dinamicamente para listar modelos ativos."""
        provider_key = provider.lower()
        if provider_key in self._model_cache and self._model_cache[provider_key]:
            return self._model_cache[provider_key]

        config = self.PROVIDERS.get(provider_key)
        if not config:
            return []

        models: List[str] = []

        try:
            if provider_key == "groq":
                key = os.getenv("GROQ_API_KEY", "")
                if key:
                    res = requests.get(
                        config["models_url"],
                        headers={"Authorization": f"Bearer {key}"},
                        timeout=5
                    )
                    if res.status_code == 200:
                        data = res.json().get("data", [])
                        # Filtra modelos de chat e código, descartando whisper e embeddings
                        models = [
                            m["id"] for m in data 
                            if not any(x in m["id"] for x in ["whisper", "embed", "guard", "vision"])
                        ]

            elif provider_key == "gemini":
                key = os.getenv("GEMINI_API_KEY", "")
                if key:
                    res = requests.get(
                        f"{config['models_url']}?key={key}",
                        timeout=5
                    )
                    if res.status_code == 200:
                        raw_models = res.json().get("models", [])
                        for m in raw_models:
                            # Considera apenas modelos que suportam geração de texto
                            methods = m.get("supportedGenerationMethods", [])
                            if "generateContent" in methods:
                                name = m.get("name", "").replace("models/", "")
                                if "gemini" in name and not any(x in name for x in ["embedding", "aqa", "imagen"]):
                                    models.append(name)

            elif provider_key == "ollama":
                res = requests.get(config["models_url"], timeout=3)
                if res.status_code == 200:
                    models = [m["name"] for m in res.json().get("models", [])]

        except Exception:
            pass

        # Usa os modelos de contingência se a consulta à API falhar
        final_models = models if models else config.get("fallback_models", [])
        self._model_cache[provider_key] = final_models
        return final_models

    def register_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        url = f"{self.supabase_url}/auth/v1/signup"
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }
        payload = {"email": email, "password": password, "data": {"name": name}}
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code not in (200, 201):
            err_data = res.json()
            raise RuntimeError(err_data.get("msg") or err_data.get("error_description") or "Erro ao registrar usuário.")
        
        data = res.json()
        user = data.get("user") or data
        return {"id": user.get("id"), "email": user.get("email"), "name": name}

    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        url = f"{self.supabase_url}/auth/v1/token?grant_type=password"
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }
        payload = {"email": email, "password": password}
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code != 200:
            err_data = res.json()
            raise RuntimeError(err_data.get("error_description") or "E-mail ou senha incorretos.")
        
        data = res.json()
        user_meta = data.get("user", {}).get("user_metadata", {})
        return {
            "access_token": data.get("access_token"),
            "id": data.get("user", {}).get("id"),
            "email": data.get("user", {}).get("email"),
            "name": user_meta.get("name", "Operador"),
        }

    def generate_command(
        self,
        prompt: str,
        provider: str = "groq",
        model: Optional[str] = None,
    ) -> str:
        provider_key = provider.lower()
        if provider_key not in self.PROVIDERS:
            provider_key = "groq"

        config = self.PROVIDERS[provider_key]
        
        # Garante que o modelo escolhido existe ou seleciona o primeiro disponível
        available = self.fetch_live_models(provider_key)
        if model and model in available:
            selected_model = model
        elif available:
            selected_model = available[0]
        else:
            selected_model = config["default_model"]

        url = config["url"]
        headers = {"Content-Type": "application/json"}

        if provider_key != "ollama":
            env_var = f"{provider_key.upper()}_API_KEY"
            key = os.getenv(env_var, "")
            if not key:
                raise ValueError(f"Chave ausente para '{provider_key}'. Defina {env_var} no .env.")
            headers["Authorization"] = f"Bearer {key}"

        system_prompt = (
            "Você é o motor de execução do ShellBase. Converta comandos em linguagem natural "
            "estritamente em cmdlets e scripts diretos de PowerShell ou CLI do Windows.\n"
            "REGRAS:\n"
            "1. Retorne APENAS o comando puro de terminal.\n"
            "2. Não use blocos de código com markdown (sem ```powershell ou ```).\n"
            "3. Não inclua comentários adicionais ou saudações.\n"
        )

        payload = {
            "model": selected_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 300,
        }

        timeout = 15 if provider_key != "ollama" else 45
        res = requests.post(url, headers=headers, json=payload, timeout=timeout)
        
        if res.status_code != 200:
            err_text = res.text
            try:
                err_text = res.json().get("error", {}).get("message", res.text)
            except Exception:
                pass
            raise RuntimeError(f"Erro {res.status_code} [{provider_key.upper()}]: {err_text}")

        data = res.json()
        command = data["choices"][0]["message"]["content"].strip()

        if command.startswith("```"):
            lines = command.splitlines()
            command = "\n".join([line for line in lines if not line.strip().startswith("```")]).strip()

        return command

    def execute_powershell(self, command: str) -> ExecutionResult:
        start = time.time()
        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                capture_output=True,
                text=True,
                timeout=30,
            )
            duration = int((time.time() - start) * 1000)
            return ExecutionResult(
                command=command,
                output=proc.stdout.strip(),
                error=proc.stderr.strip(),
                duration_ms=duration,
                success=(proc.returncode == 0),
            )
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            return ExecutionResult(
                command=command,
                output="",
                error=str(e),
                duration_ms=duration,
                success=False,
            )

    def log_execution(
        self,
        prompt: str,
        result: ExecutionResult,
        user_email: Optional[str] = None,
        user_name: Optional[str] = None
    ):
        if not self.supabase_url or not self.supabase_key:
            return
        try:
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "prompt": prompt,
                "generated_command": result.command,
                "output": result.output[:2000],
                "error": result.error[:2000],
                "duration_ms": result.duration_ms,
                "success": result.success,
                "user_email": user_email or "Anônimo",
                "user_name": user_name or "Desconhecido",
            }
            requests.post(f"{self.supabase_url}/rest/v1/execution_logs", headers=headers, json=payload, timeout=3)
        except Exception:
            pass