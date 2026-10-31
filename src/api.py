import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.resolve()))
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core import ShellBaseEngine, SecurityFilter

app = FastAPI(title="ShellBase Core API")

# Libera chamadas locais vindas do app desktop
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializa o motor com as suas credenciais
engine = ShellBaseEngine(
    supabase_url="https://ftmoqhnzmzpanggntysa.supabase.co",
    supabase_key="sb_publishable_wNyiObnZX5jcWaQRf1aTWA_I9nPM74m",
    llm_model="qwen2.5-coder:7b",
)

class PromptRequest(BaseModel):
    prompt: str

class ExecuteRequest(BaseModel):
    command: str
    prompt: str

@app.post("/generate")
def generate_command(req: PromptRequest):
    try:
        embedding = engine.get_embedding(req.prompt)
        context = engine.retrieve_context(embedding, top_k=3)
        command = engine.generate_command(req.prompt, context)
        
        allowed, warning = SecurityFilter.analyze(command)
        
        return {
            "command": command,
            "allowed": allowed,
            "warning": warning,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute")
def execute_command(req: ExecuteRequest):
    try:
        result = engine.execute_powershell(req.command)
        engine.log_execution(req.prompt, result)
        
        return {
            "output": result.output,
            "error": result.error,
            "duration_ms": result.duration_ms,
            "success": result.success,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))