import sys
from src.core import ShellBaseEngine, SecurityFilter

SUPABASE_URL = "https://ftmoqhnzmzpanggntysa.supabase.co"
SUPABASE_KEY = "sb_publishable_wNyiObnZX5jcWaQRf1aTWA_I9nPM74m"

def run_cli():
    print("==================================================")
    print("                   SHELLBASE                      ")
    print("==================================================")

    engine = ShellBaseEngine(
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY,
        llm_model="qwen2.5-coder:1.5b"
    )

    while True:
        try:
            prompt = input("\n[ShellBase] Digite a tarefa de TI (ou 'sair'): ").strip()
            if not prompt:
                continue
            if prompt.lower() in ["sair", "exit", "quit"]:
                print("Encerrando execução.")
                break

            print("[1/3] Consultando documentação (RAG)...")
            embedding = engine.get_embedding(prompt)
            context = engine.retrieve_context(embedding, top_k=3)

            print("[2/3] Gerando script ...")
            command = engine.generate_command(prompt, context)

            print("\n" + "=" * 50)
            print("SCRIPT PROPOSTO:")
            print("=" * 50)
            print(command)
            print("=" * 50)

            # Análise de segurança
            allowed, warning_msg = SecurityFilter.analyze(command)
            if not allowed:
                print(f"\n[BLOQUEADO] {warning_msg}")
                continue

            if warning_msg:
                print(f"\n[ATENÇÃO] {warning_msg}")

            confirm = input("\nAutorizar execução? (y/N): ").strip().lower()
            if confirm not in ["y", "s", "sim", "yes"]:
                print("Execução abortada pelo operador.")
                continue

            print("\n[3/3] Executando comando no PowerShell...")
            result = engine.execute_powershell(command)

            if result.success:
                print("\n--- SAÍDA DO POWERSHELL ---")
                print(result.output if result.output else "(Sucesso - sem retorno em texto)")
            else:
                print("\n--- ERRO ---")
                print(result.error)

            print(f"\nTempo decorrido: {result.duration_ms} ms | Status: {'OK' if result.success else 'FALHA'}")

            # Registra no Supabase
            engine.log_execution(prompt, result)

        except KeyboardInterrupt:
            print("\nSessão finalizada pelo usuário.")
            break
        except Exception as e:
            print(f"\n[ERRO]: {e}")

if __name__ == "__main__":
    run_cli()
