# Project-P0 — Resumo de Anotações com Ollama

Aplicação Python para transformar anotações soltas de reuniões ou aulas em um resumo estruturado com pontos-chave, decisões e tarefas.

## Pré-requisitos

- Python 3.11 ou superior
- Conexão com um servidor Ollama acessível
- PowerShell, terminal Linux ou macOS

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configuração de acesso

O programa lê variáveis de ambiente. Não coloque credenciais reais no repositório.

| Variável | Obrigatória | Padrão | Finalidade |
|---|---:|---|---|
| `OLLAMA_HOST` | Não | `https://llm-internal.softex:9001` | Endereço base do Ollama |
| `OLLAMA_MODEL` | Não | `qwen3.5` | Modelo usado na chamada |
| `OLLAMA_TIMEOUT` | Não | `300` | Timeout em segundos |
| `OLLAMA_REQUIRE_AUTH` | Não | `false` | Exige `OLLAMA_API_KEY` localmente |
| `OLLAMA_API_KEY` | Apenas se exigida | vazio | Credencial opcional enviada como Bearer |

Exemplo PowerShell:

```powershell
$env:OLLAMA_HOST = "https://llm-internal.softex:9001"
$env:OLLAMA_MODEL = "qwen3.5"
$env:OLLAMA_REQUIRE_AUTH = "false"
$env:OLLAMA_API_KEY = ""
$env:OLLAMA_TIMEOUT = "300"
```

O arquivo `.env.example` contém um modelo sem credenciais reais. Ele não é carregado automaticamente pelo programa; as variáveis devem ser exportadas no terminal ou configuradas pelo ambiente do container.

O Ollama institucional usado neste projeto pode utilizar HTTPS com certificado autogerado. A chamada utiliza `verify=False` apenas para esse contexto interno. Em serviços públicos, prefira um certificado confiável e `verify=True`.

## Execução no terminal

```powershell
python main.py
```

Cole as anotações, confirme uma linha vazia e aguarde o modelo.

### Exemplo de entrada

```text
Reunião de terça com Ana e Carlos.
Decidiram lançar o formulário até sexta.
Carlos envia o texto até quarta.
Ana verifica a integração com o sistema.
```

### Exemplo de saída

```markdown
# Resumo Executivo
Foi definida a preparação e o lançamento de um formulário.

# Pontos-chave
- Participantes: Ana e Carlos

# Decisões tomadas
- O formulário será lançado até sexta-feira

# Lista de tarefas
- [ ] Carlos — enviar o texto — até quarta-feira
- [ ] Ana — verificar a integração com o sistema — prazo não informado
```

A saída real depende do modelo e do texto fornecido.

## Organização do código

`main.py` separa as responsabilidades em funções:

- `load_configuration`: configurações e validações;
- `capture_text`: entrada pelo terminal;
- `prepare_chat_request`: preparação do JSON;
- `call_llm`: comunicação HTTP e tradução de falhas;
- `parse_response`: validação da resposta;
- `present_result`: apresentação ao usuário.

## Tratamento de erros

O programa reconhece e explica:

- entrada vazia;
- endereço ou timeout inválido;
- credencial ausente quando a autenticação é exigida;
- credencial rejeitada com HTTP 401/403;
- endereço ou modelo indisponível;
- timeout;
- falha de conexão;
- HTTP 429 e 5xx;
- resposta vazia, não JSON ou com formato inesperado.

As mensagens apontam o problema sem imprimir credenciais.

## Testes

Execute:

```powershell
python -m unittest -v
```

Os testes simulados cobrem:

- entrada vazia;
- configuração inválida;
- credencial ausente;
- credencial inválida via HTTP 401;
- timeout;
- serviço indisponível via HTTP 503;
- resposta vazia ou inesperada.

Os testes são mockados para evitar dependência externa e não contêm credenciais reais.

## Teste real do LLM

Com acesso ao servidor Ollama, execute:

```powershell
python main.py
```

Quando a infraestrutura institucional estiver disponível, o teste real pode ser feito informando `OLLAMA_HOST` e `OLLAMA_MODEL`. A recuperação do serviço externo continua sendo responsabilidade da equipe técnica.

## Interface web opcional

```powershell
streamlit run app.py --server.port=80 --server.address=0.0.0.0
```

## Docker

Consulte `BUILD_AND_DEPLOY.md` para build, exportação da imagem e configuração no Devel LLM Portal.

## Dependências

- `requests`: chamadas HTTP ao Ollama
- `streamlit`: interface web opcional
