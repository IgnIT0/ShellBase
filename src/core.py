import os
import re
import subprocess
import time
from dataclasses import dataclass
from typing import Optional, Tuple
import requests
from supabase import Client, create_client


@dataclass
class ExecutionResult:
    command: str
    output: str
    error: Optional[str]
    return_code: int
    duration_ms: int
    success: bool


class SecurityFilter:

    BLOCKED_PATTERNS = [
        r"format-volume",
        r"format-partition",
        r"clear-disk",
        r"remove-item\s+.*system32",
        r"remove-item\s+.*c:\\windows",
        r"stop-computer\s+-force",
        r"bcdedit\s+/delete",
    ]

    WARN_PATTERNS = [
        r"restart-computer",
        r"stop-computer",
        r"remove-aduser",
        r"remove-item",
        r"set-service.*disabled",
    ]

    @classmethod
    def analyze(cls, command: str) -> Tuple[bool, Optional[str]]:
        cmd_lower = command.lower()

        for pattern in cls.BLOCKED_PATTERNS:
            if re.search(pattern, cmd_lower):
                return False, f"Comando bloqueado por política de segurança: padrão crítico '{pattern}' detectado."

        for pattern in cls.WARN_PATTERNS:
            if re.search(pattern, cmd_lower):
                return True, f"Aviso: este comando realiza alterações destrutivas ou encerramento de serviços."

        return True, None


class ShellBaseEngine:
    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        ollama_url: str = "http://localhost:11434",
        embed_model: str = "nomic-embed-text",
        llm_model: str = "qwen2.5-coder:7b",
    ):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.ollama_url = ollama_url.rstrip("/")
        self.embed_model = embed_model
        self.llm_model = llm_model

    def get_embedding(self, text: str) -> list[float]:
        """Gera o vetor semântico do prompt do operador."""
        url = f"{self.ollama_url}/api/embeddings"
        payload = {"model": self.embed_model, "prompt": text[:2000]}
        
        try:
            res = requests.post(url, json=payload, timeout=15)
            res.raise_for_status()
            return res.json().get("embedding", [])
        except Exception as e:
            raise RuntimeError(f"Falha ao gerar embedding: {e}")

    def retrieve_context(self, embedding: list[float], top_k: int = 5, threshold: float = 0.25) -> str:
        """Busca os comandos mais aderentes no Supabase pgvector."""
        try:
            res = self.supabase.rpc(
                "match_powershell_docs",
                {
                    "query_embedding": embedding,
                    "match_threshold": threshold,
                    "match_count": top_k,
                },
            ).execute()

            docs = res.data or []
            if not docs:
                return "Nenhum cmdlet específico encontrado no repositório de documentação."

            context_blocks = []
            for d in docs:
                context_blocks.append(
                    f"Cmdlet: {d['cmdlet_name']}\n"
                    f"Módulo: {d['module_name']}\n"
                    f"Descrição: {d['description']}\n"
                    f"Sintaxe:\n{d['syntax']}"
                )
            return "\n\n---\n\n".join(context_blocks)
        except Exception as e:
            raise RuntimeError(f"Erro na consulta vetorial ao Banco de Dados: {e}")

    def generate_command(self, user_prompt: str, context: str) -> str:
        """Solicita ao LLM o script PowerShell otimizado com base na documentação."""
        system_rules = (
            "Você é o motor de automação do ShellBase, especialista em PowerShell corporativo.\n"
            "Diretrizes de geração:\n"
            "1. Retorne APENAS o script PowerShell puro e executável, sem blocos de texto ou explicações.\n"
            "2. Para o nome da máquina, NUNCA use $Host.Name (que retorna ConsoleHost). Use SEMPRE $env:COMPUTERNAME.\n"
            "3. Em diagnósticos de rede e IP, ignore adaptadores virtuais de VPN/WSL: filtre adaptadores físicos com ($_.Virtual -eq $false) ou pegue o adaptador associado ao Gateway padrão ativo.\n"
            "4. Priorize filtros no próprio cmdlet (ex: -Filter) em vez de pipelines Where-Object lentos.\n"
            "5. Use objetos estruturados ([PSCustomObject]) ou Format-Table/Format-List para saídas legíveis.\n"
        )

        prompt_payload = (
            f"{system_rules}\n"
            f"=== DOCUMENTAÇÃO DE REFERÊNCIA (RAG) ===\n{context}\n\n"
            f"=== REQUISIÇÃO DO TÉCNICO ===\n{user_prompt}\n\n"
            f"=== CÓDIGO POWERSHELL ==="
        )

        url = f"{self.ollama_url}/api/generate"
        payload = {"model": self.llm_model, "prompt": prompt_payload, "stream": False}

        try:
            res = requests.post(url, json=payload, timeout=180)
        
        # Se retornar erro (404, 500, etc.), exibe o corpo exato da resposta
            if res.status_code != 200:
                print(f"\n[DEBUG OLLAMA] Status: {res.status_code}")
                print(f"[DEBUG OLLAMA] Resposta bruta: {res.text}\n")
                res.raise_for_status()

            raw_output = res.json().get("response", "").strip()

            if raw_output.startswith("```"):
                lines = raw_output.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
                raw_output = "\n".join(lines).strip()

            return raw_output
        except Exception as e:
            raise RuntimeError(f"Falha na inferência com {self.llm_model}: {e}")

    def execute_powershell(self, script: str) -> ExecutionResult:
        """Executa o script de forma isolada e mede o tempo de resposta."""
        start = time.perf_counter()

        process = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        duration_ms = int((time.perf_counter() - start) * 1000)
        success = (process.returncode == 0)

        return ExecutionResult(
            command=script,
            output=process.stdout.strip(),
            error=process.stderr.strip() if not success else None,
            return_code=process.returncode,
            duration_ms=duration_ms,
            success=success,
        )

    def log_execution(self, prompt: str, result: ExecutionResult):
        """Persiste a telemetria no Supabase para datasets de Fine-Tuning futuros."""
        try:
            self.supabase.table("execution_logs").insert(
                {
                    "user_prompt": prompt,
                    "generated_script": result.command,
                    "execution_time_ms": result.duration_ms,
                    "success": result.success,
                }
            ).execute()
        except Exception as e:
            print(f"[AVISO] Falha ao persistir telemetria: {e}")