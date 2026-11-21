import os
import sys

import requests
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "https://llm-internal.softex:9001",
).rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5")

SYSTEM_PROMPT = """Você é um assistente especializado em transformar anotações soltas e desorganizadas de reuniões ou aulas em conteúdo claro e útil.

Organize a resposta em português do Brasil com:
1. Resumo executivo
2. Pontos-chave
3. Decisões tomadas
4. Lista de tarefas

Não invente informações ausentes e preserve nomes, datas e prazos explicitamente mencionados."""


def fetch_model() -> str:
    """Busca o modelo configurado ou o primeiro modelo disponível no Ollama."""
    try:
        response = requests.get(
            f"{OLLAMA_HOST}/api/tags",
            verify=False,
            timeout=15,
        )
        response.raise_for_status()
        models = response.json().get("models", [])

        if any(model.get("name") == OLLAMA_MODEL for model in models):
            return OLLAMA_MODEL

        available = [model["name"] for model in models if model.get("name")]
        if available:
            print(f"Modelo '{OLLAMA_MODEL}' não encontrado. Usando '{available[0]}'.")
            return available[0]
    except (requests.RequestException, ValueError):
        pass

    print(f"Não foi possível consultar os modelos. Usando '{OLLAMA_MODEL}'.")
    return OLLAMA_MODEL


def generate_summary(model: str, text: str) -> str:
    """Envia as anotações ao Ollama e retorna o conteúdo gerado."""
    response = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "stream": False,
            "options": {"temperature": 0.1},
        },
        verify=False,
        timeout=300,
    )
    response.raise_for_status()

    message = response.json().get("message", {})
    answer = message.get("content", "").strip()
    if not answer:
        raise RuntimeError("O modelo não retornou conteúdo.")
    return answer


def read_text_from_terminal() -> str:
    """Lê texto multilinha; o usuário finaliza com uma linha vazia."""
    print("Cole suas anotações abaixo.")
    print("Finalize enviando uma linha vazia:")

    lines = []
    while True:
        line = input()
        if not line:
            break
        lines.append(line)

    return "\n".join(lines).strip()


def main() -> int:
    text = read_text_from_terminal()
    if not text:
        print("Erro: nenhuma anotação foi fornecida.", file=sys.stderr)
        return 1

    try:
        model = fetch_model()
        print(f"\nProcessando com o modelo '{model}'...\n")
        result = generate_summary(model, text)
        print(result)
        return 0
    except requests.RequestException as exc:
        print(f"Erro ao comunicar com o Ollama: {exc}", file=sys.stderr)
        return 1
    except (RuntimeError, ValueError) as exc:
        print(f"Erro ao processar a resposta: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
