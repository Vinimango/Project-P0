# Project-P0 — Resumo de Anotações com Ollama

Aplicação Python que transforma anotações soltas de reuniões ou aulas em um resumo estruturado usando um modelo LLM disponível no Ollama.

## Fluxo básico no terminal

### 1. Criar o ambiente local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configurar o Ollama

Variáveis opcionais:

```powershell
$env:OLLAMA_HOST = "https://llm-internal.softex:9001"
$env:OLLAMA_MODEL = "qwen3.5"
```

As variáveis não são necessárias para os valores padrão definidos pelo programa.

### 3. Executar

```powershell
python main.py
```

Cole o texto no terminal e finalize com uma linha vazia.

## Interface web opcional

```powershell
streamlit run app.py --server.port=80 --server.address=0.0.0.0
```

## Dependências

- `requests`: comunicação HTTP com Ollama
- `streamlit`: interface web opcional

## Docker

Consulte `BUILD_AND_DEPLOY.md` para construir e exportar a imagem.
