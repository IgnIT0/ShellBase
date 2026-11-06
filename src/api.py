import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))

from core import ShellBaseEngine, SecurityFilter
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="ShellBase Core API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = ShellBaseEngine()

class PromptRequest(BaseModel):
    prompt: str
    provider: Optional[str] = "groq"
    model: Optional[str] = None

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ExecuteRequest(BaseModel):
    command: str
    prompt: str
    user_email: Optional[str] = None
    user_name: Optional[str] = None

@app.get("/providers")
def get_providers():
    """Retorna os provedores com os modelos detectados ao vivo."""
    providers_list = []
    for k, v in engine.PROVIDERS.items():
        live_models = engine.fetch_live_models(k)
        providers_list.append({
            "id": k,
            "name": v["name"],
            "default_model": live_models[0] if live_models else v["default_model"],
            "models": live_models
        })
    return {"providers": providers_list}

@app.post("/auth/register")
def register(req: RegisterRequest):
    try:
        user_data = engine.register_user(req.email, req.password, req.name)
        return {"success": True, "user": user_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login")
def login(req: LoginRequest):
    try:
        user_data = engine.login_user(req.email, req.password)
        return {"success": True, "user": user_data}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/generate")
def generate_command(req: PromptRequest):
    try:
        command = engine.generate_command(
            prompt=req.prompt,
            provider=req.provider or "groq",
            model=req.model
        )
        allowed, warning = SecurityFilter.analyze(command)
        return {
            "command": command,
            "allowed": allowed,
            "warning": warning,
            "provider": req.provider,
            "model": req.model,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute")
def execute_command(req: ExecuteRequest):
    try:
        result = engine.execute_powershell(req.command)
        engine.log_execution(
            prompt=req.prompt,
            result=result,
            user_email=req.user_email,
            user_name=req.user_name
        )
        return {
            "output": result.output,
            "error": result.error,
            "duration_ms": result.duration_ms,
            "success": result.success,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))