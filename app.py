import json
import os
from datetime import datetime
from pathlib import Path

import requests
import streamlit as st
import urllib3

from execution_log import log_execution


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://llm-internal.softex:9001").rstrip("/")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "").strip() or None
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))
PERSISTENT_DIR = Path("/persistent")
HISTORY_FILE = PERSISTENT_DIR / "historico.json"
DEFAULT_MODEL = "qwen3.5"

SYSTEM_PROMPT = """Você é um assistente especializado em transformar anotações soltas e desorganizadas de reuniões ou aulas em conteúdo claro e útil.

Analise todo o texto enviado e devolva exclusivamente um resumo em Markdown com esta estrutura:

# Resumo Executivo
Uma síntese curta e objetiva do conteúdo.

# Pontos-chave
- ponto relevante

# Decisões Tomadas
- decisão tomada, ou `Nenhuma decisão registrada` quando não houver decisões claras

# Tarefas
- [ ] Responsável — tarefa — prazo, quando essas informações estiverem presentes

# Próximos Passos
- próximos passos sugeridos a partir das informações disponíveis

Regras:
- Preserve nomes, datas, prazos e decisões que estiverem explícitos.
- Não invente informações ausentes.
- Use linguagem profissional, direta e em português do Brasil.
- Não acrescente comentários fora do documento Markdown solicitado."""


def ensure_persistent_storage() -> None:
    try:
        PERSISTENT_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        fallback = Path.cwd() / "persistent"
        fallback.mkdir(parents=True, exist_ok=True)


def get_history_file() -> Path:
    try:
        PERSISTENT_DIR.mkdir(parents=True, exist_ok=True)
        return HISTORY_FILE
    except OSError:
        fallback = Path.cwd() / "persistent"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback / "historico.json"


def load_history() -> list:
    path = get_history_file()
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_history(entry: dict) -> bool:
    path = get_history_file()
    history = load_history()
    history.insert(0, entry)
    history = history[:50]
    try:
        with path.open("w", encoding="utf-8") as file:
            json.dump(history, file, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def fetch_models() -> list:
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", verify=False, timeout=15)
        response.raise_for_status()
        payload = response.json()
        models = [item["name"] for item in payload.get("models", []) if item.get("name")]
        if models:
            return sorted(set(models))
    except (requests.RequestException, ValueError):
        pass
    return [DEFAULT_MODEL]


def analyze_text(model: str, text: str, temperature: float = 0.1, num_predict: int = 50, top_p: float = 1.0) -> str:
    headers = {"Content-Type": "application/json"}
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

    response = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
                "top_p": top_p,
            },
        },
        headers=headers,
        verify=False,
        timeout=OLLAMA_TIMEOUT,
    )

    if response.status_code in (401, 403):
        raise RuntimeError("A credencial foi rejeitada pelo Ollama. Verifique OLLAMA_API_KEY.")
    if response.status_code == 404:
        try:
            server_message = response.json().get("error", "")
        except ValueError:
            server_message = ""
        detail = f" Detalhe: {server_message}" if server_message else ""
        raise RuntimeError(
            f"O Ollama não encontrou o endpoint ou o modelo '{model}'. "
            f"Selecione um modelo disponível na barra lateral.{detail}"
        )
    if response.status_code == 429:
        raise RuntimeError("O Ollama está limitando solicitações. Aguarde e tente novamente.")
    if response.status_code >= 500:
        raise RuntimeError("O serviço Ollama está indisponível no momento. Tente novamente mais tarde.")

    try:
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        raise RuntimeError(
            f"O Ollama rejeitou a solicitação com o status HTTP {response.status_code}."
        )
    except ValueError:
        raise RuntimeError("O Ollama respondeu, mas o formato da resposta não é JSON válido.")

    if not isinstance(payload, dict):
        raise RuntimeError("O Ollama respondeu em formato inesperado.")
    message = payload.get("message")
    if not isinstance(message, dict):
        raise RuntimeError("A resposta do Ollama não contém o campo 'message' esperado.")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("O modelo respondeu, mas o conteúdo está vazio.")
    return content.strip()


ensure_persistent_storage()
st.set_page_config(page_title="Resumo de Reuniões", page_icon="📝", layout="wide")

st.title("📝 Transformador de Anotações")
st.caption("Transforme notas soltas de reuniões ou aulas em um resumo estruturado.")

with st.sidebar:
    st.header("Configuração")
    models = fetch_models()
    default_index = models.index(DEFAULT_MODEL) if DEFAULT_MODEL in models else 0
    model = st.selectbox("Modelo Ollama", models, index=default_index)
    st.caption(f"Servidor: `{OLLAMA_HOST}`")
    temperature = st.slider("Temperatura", 0.0, 1.0, 0.1, 0.01)
    num_predict = st.slider("Limite de tokens", 1, 500, 50)
    top_p = st.slider("Top P", 0.0, 1.0, 1.0, 0.01)

col_input, col_output = st.columns(2, gap="large")

with col_input:
    st.subheader("Anotações")
    source_text = st.text_area(
        "Cole aqui o conteúdo bruto",
        height=420,
        placeholder="Ex.: Na reunião de segunda, decidimos lançar a nova página até sexta...",
    )
    process = st.button("Gerar resumo", type="primary", use_container_width=True)

with col_output:
    st.subheader("Resultado")
    if "result_markdown" not in st.session_state:
        st.session_state.result_markdown = ""

    if process:
        if not source_text.strip():
            st.warning("Cole o texto que deseja transformar.")
        else:
            with st.spinner("Processando com o Ollama..."):
                try:
                    result = analyze_text(model, source_text, temperature, num_predict, top_p)
                    if not result:
                        raise RuntimeError("O modelo não retornou conteúdo.")
                    st.session_state.result_markdown = result
                    saved = save_history(
                        {
                            "timestamp": datetime.now().isoformat(timespec="seconds"),
                            "model": model,
                            "source": source_text,
                            "result": result,
                        }
                    )
                    log_execution("chat", model=model, status="success")
                    if not saved:
                        st.warning("Não foi possível salvar esta análise no histórico persistente.")
                except requests.RequestException as exc:
                    log_execution("CommunicationError", model=model, status="error")
                    st.error(f"Falha ao comunicar com o Ollama: {exc}")
                except (ValueError, RuntimeError) as exc:
                    log_execution(exc.__class__.__name__, model=model, status="error")
                    st.error(str(exc))

    if st.session_state.result_markdown:
        st.markdown(st.session_state.result_markdown)
        st.download_button(
            "Baixar resultado (.md)",
            data=st.session_state.result_markdown,
            file_name="resumo.md",
            mime="text/markdown",
            use_container_width=True,
        )

st.divider()
st.subheader("Histórico de análises")
history = load_history()
if not history:
    st.info("Nenhuma análise salva ainda.")
else:
    for index, item in enumerate(history):
        title = f'{item.get("timestamp", "Sem data")} — {item.get("model", "Modelo desconhecido")}'
        with st.expander(title, expanded=False):
            st.markdown("**Anotações originais**")
            st.text(item.get("source", ""))
            st.markdown("**Resumo**")
            st.markdown(item.get("result", ""))
