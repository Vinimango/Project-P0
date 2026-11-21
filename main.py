import os
import sys
from dataclasses import dataclass

import requests
import urllib3

from execution_log import log_execution


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_OLLAMA_HOST = "https://llm-internal.softex:9001"
DEFAULT_OLLAMA_MODEL = "qwen3.5"

SYSTEM_PROMPT = """Você é um assistente especializado em transformar anotações soltas e desorganizadas de reuniões ou aulas em conteúdo claro e útil.

Organize a resposta em português do Brasil com:
1. Resumo executivo
2. Pontos-chave
3. Decisões tomadas
4. Lista de tarefas

Não invente informações ausentes e preserve nomes, datas e prazos explicitamente mencionados."""


class ConfigurationError(Exception):
    pass


class EmptyInputError(Exception):
    pass


class AuthenticationError(Exception):
    pass


class LLMUnavailableError(Exception):
    pass


class CommunicationError(Exception):
    pass


class ResponseFormatError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    host: str
    model: str
    api_key: str | None
    require_auth: bool
    timeout_seconds: float
    temperature: float
    num_predict: int
    top_p: float


def load_configuration(environ: dict | None = None) -> Config:
    """Responsabilidade: carregar e validar as configurações do ambiente."""
    env = os.environ if environ is None else environ
    host = env.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST).strip().rstrip("/")
    model = env.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL).strip()
    api_key = env.get("OLLAMA_API_KEY", "").strip() or None

    require_auth = env.get("OLLAMA_REQUIRE_AUTH", "false").strip().lower() in {
        "1", "true", "yes", "on"
    }

    try:
        timeout_seconds = float(env.get("OLLAMA_TIMEOUT", "300"))
        temperature = float(env.get("OLLAMA_TEMPERATURE", "0.1"))
        num_predict = int(env.get("OLLAMA_NUM_PREDICT", "100"))
        top_p = float(env.get("OLLAMA_TOP_P", "1.0"))
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            "OLLAMA_TIMEOUT, OLLAMA_TEMPERATURE, OLLAMA_NUM_PREDICT e OLLAMA_TOP_P "
            "devem conter números válidos."
        ) from exc

    if not host:
        raise ConfigurationError("OLLAMA_HOST está vazio.")
    if not host.startswith(("http://", "https://")):
        raise ConfigurationError(
            "OLLAMA_HOST inválido. Use um endereço começando com http:// ou https://."
        )
    if not model:
        raise ConfigurationError("OLLAMA_MODEL está vazio.")
    if timeout_seconds <= 0:
        raise ConfigurationError("OLLAMA_TIMEOUT deve ser maior que zero.")
    if not 0.0 <= temperature <= 2.0:
        raise ConfigurationError("OLLAMA_TEMPERATURE deve estar entre 0 e 2.")
    if num_predict <= 0:
        raise ConfigurationError("OLLAMA_NUM_PREDICT deve ser maior que zero.")
    if not 0.0 <= top_p <= 1.0:
        raise ConfigurationError("OLLAMA_TOP_P deve estar entre 0 e 1.")
    if require_auth and not api_key:
        raise AuthenticationError(
            "Autenticação solicitada, mas OLLAMA_API_KEY não foi configurada."
        )

    return Config(
        host, model, api_key, require_auth, timeout_seconds,
        temperature, num_predict, top_p
    )


def capture_text(input_function=input) -> str:
    """Responsabilidade: receber a entrada pelo terminal."""
    print("Cole suas anotações abaixo.")
    print("Finalize enviando uma linha vazia:")

    lines = []
    try:
        while True:
            line = input_function()
            if not line:
                break
            lines.append(line)
    except EOFError as exc:
        raise EmptyInputError(
            "Nenhuma anotação foi informada antes do fim da entrada."
        ) from exc

    text = "\n".join(lines).strip()
    if not text:
        raise EmptyInputError(
            "Nenhuma anotação foi informada. Cole um texto antes de processar."
        )
    return text


def prepare_chat_request(config: Config, text: str) -> dict:
    """Responsabilidade: preparar o corpo da solicitação ao Ollama."""
    return {
        "model": config.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "stream": False,
        "options": {
            "temperature": config.temperature,
            "num_predict": config.num_predict,
            "top_p": config.top_p,
        },
    }


def prepare_headers(config: Config) -> dict:
    headers = {"Content-Type": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"
    return headers


def call_llm(config: Config, payload: dict) -> dict:
    """Responsabilidade: realizar a comunicação HTTP e traduzir falhas previsíveis."""
    try:
        response = requests.post(
            f"{config.host}/api/chat",
            json=payload,
            headers=prepare_headers(config),
            verify=False,
            timeout=config.timeout_seconds,
        )
    except requests.Timeout as exc:
        raise CommunicationError(
            f"O modelo demorou mais que {config.timeout_seconds:g} segundos para responder. "
            "Tente novamente; se continuar, consulte a equipe técnica responsável pelo Ollama."
        ) from exc
    except requests.ConnectionError as exc:
        raise CommunicationError(
            f"Não foi possível conectar ao servidor Ollama em {config.host}. "
            "Verifique a rede e a disponibilidade do serviço."
        ) from exc
    except requests.RequestException as exc:
        raise CommunicationError(
            "Ocorreu uma falha ao comunicar com o serviço Ollama."
        ) from exc

    if response.status_code in (401, 403):
        raise AuthenticationError(
            "A credencial foi rejeitada pelo serviço Ollama. "
            "Confirme OLLAMA_API_KEY e a autenticação exigida pelo servidor."
        )
    if response.status_code == 404:
        raise LLMUnavailableError(
            f"O modelo ou o endereço '{config.model}' não está disponível. "
            "Confirme OLLAMA_HOST e o nome do modelo."
        )
    if response.status_code == 429:
        raise LLMUnavailableError(
            "O serviço Ollama está limitando solicitações temporariamente. Aguarde e tente novamente."
        )
    if response.status_code >= 500:
        raise LLMUnavailableError(
            "O serviço Ollama está indisponível no momento. "
            "Tente novamente mais tarde; a recuperação da infraestrutura é responsabilidade da equipe técnica."
        )
    if response.status_code >= 400:
        raise CommunicationError(
            f"O Ollama rejeitou a solicitação com o status HTTP {response.status_code}."
        )

    try:
        return response.json()
    except ValueError as exc:
        raise ResponseFormatError(
            "O Ollama respondeu, mas não enviou uma resposta JSON válida."
        ) from exc


def parse_response(payload: dict) -> str:
    """Responsabilidade: validar e extrair a resposta esperada."""
    if not isinstance(payload, dict):
        raise ResponseFormatError("A resposta do Ollama deve ser um objeto JSON.")

    message = payload.get("message")
    if not isinstance(message, dict):
        raise ResponseFormatError(
            "A resposta não contém o campo 'message' no formato esperado."
        )

    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ResponseFormatError(
            "O modelo respondeu, mas o campo de conteúdo está vazio ou possui formato inesperado."
        )
    return content.strip()


def present_result(result: str) -> None:
    """Responsabilidade: apresentar somente o resultado útil ao usuário."""
    print("\n--- Resumo gerado pelo modelo ---\n")
    print(result)


def main() -> int:
    try:
        config = load_configuration()
        text = capture_text()
        payload = prepare_chat_request(config, text)
        response_payload = call_llm(config, payload)
        result = parse_response(response_payload)
        present_result(result)
        log_execution("chat", model=config.model, status="success")
        return 0
    except (
        ConfigurationError,
        EmptyInputError,
        AuthenticationError,
        LLMUnavailableError,
        CommunicationError,
        ResponseFormatError,
    ) as exc:
        error_name = exc.__class__.__name__
        log_execution(error_name, status="error")
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        log_execution("KeyboardInterrupt", status="cancelled")
        print("\nOperação cancelada pelo usuário.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
