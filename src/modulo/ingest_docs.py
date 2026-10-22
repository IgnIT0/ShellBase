import json
import time
import requests
from supabase import Client, create_client

#CONFIGURAÇÕES

SUPABASE_URL = "https://ftmoqhnzmzpanggntysa.supabase.co"
SUPABASE_KEY = "sb_publishable_wNyiObnZX5jcWaQRf1aTWA_I9nPM74m"  
OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
JSON_FILE_PATH = "powershell_docs.json"
BATCH_SIZE = 50  

# Inicializa o cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_embedding(text: str) -> list[float]:
    """Solicita a geração do vetor de embedding ao Ollama local."""
    payload = {"model": EMBED_MODEL, "prompt": text}
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json().get("embedding", [3000])
    except Exception as e:
        print(f"\n[ERRO] Falha ao gerar embedding via Ollama: {e}")
        return []


def main():
    print(f"Lendo o arquivo '{JSON_FILE_PATH}'...")
    try:
        with open(JSON_FILE_PATH, "r", encoding="utf-8-sig") as f:
            docs = json.load(f)
    except FileNotFoundError:
        print(
            f"[ERRO] O arquivo {JSON_FILE_PATH} não foi encontrado no diretório atual."
        )
        return

    total_docs = len(docs)
    print(f"Total de comandos a processar: {total_docs}\n")

    batch = []
    inserted_count = 0

    for i, item in enumerate(docs, 1):
        content_text = item.get("content_text", "")
        if not content_text:
            continue

        # Generates vector via Ollama
        embedding = get_embedding(content_text)
        if not embedding:
            print(f"Pulando {item.get('cmdlet_name')} por erro no vetor.")
            continue

        record = {
            "cmdlet_name": item.get("cmdlet_name"),
            "module_name": item.get("module_name"),
            "syntax": item.get("syntax"),
            "description": item.get("description"),
            "embedding": embedding,
        }
        batch.append(record)

        # Envia em lote ao atingir a quantidade definida ou no último elemento
        if len(batch) >= BATCH_SIZE or i == total_docs:
            try:
                supabase.table("powershell_docs").insert(batch).execute()
                inserted_count += len(batch)
                print(
                    f"Progresso: [{i}/{total_docs}] - {inserted_count} comandos inseridos no Supabase."
                )
            except Exception as e:
                print(f"\n[ERRO] Falha ao inserir lote no Supabase: {e}")

            batch = []  # Limpa o lote processado

        time.sleep(0.01)

    print(
        f"\nProcesso concluído, {inserted_count} de {total_docs} comandos armazenados com sucesso."
    )


if __name__ == "__main__":
    main()
