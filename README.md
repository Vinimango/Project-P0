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

| Variável              |       Obrigatória | Padrão                             | Finalidade                              |
| --------------------- | ----------------: | ---------------------------------- | --------------------------------------- |
| `OLLAMA_HOST`         |               Não | `https://llm-internal.softex:9001` | Endereço base do Ollama                 |
| `OLLAMA_MODEL`        |               Não | `qwen3.5`                          | Modelo usado na chamada                 |
| `OLLAMA_TIMEOUT`      |               Não | `300`                              | Timeout em segundos                     |
| `OLLAMA_REQUIRE_AUTH` |               Não | `false`                            | Exige `OLLAMA_API_KEY` localmente       |
| `OLLAMA_API_KEY`      | Apenas se exigida | vazio                              | Credencial opcional enviada como Bearer |

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

## Parâmetros avançados da geração

Os parâmetros seguintes podem ser alterados sem modificar o núcleo da aplicação:

| Variável             | Padrão | Limite                 | Uso                                 |
| -------------------- | -----: | ---------------------- | ----------------------------------- |
| `OLLAMA_TEMPERATURE` |  `0.1` | `0.0` a `2.0`          | Controle de aleatoriedade           |
| `OLLAMA_NUM_PREDICT` |  `100` | inteiro maior que zero | Limite aproximado de tokens gerados |
| `OLLAMA_TOP_P`       |  `1.0` | `0.0` a `1.0`          | Diversidade acumulada da amostragem |

Na interface Streamlit, os mesmos controles estão disponíveis na barra lateral:

- Temperatura;
- Limite de tokens;
- Top P.

A chave `OLLAMA_API_KEY` continua sendo lida apenas do ambiente e nunca aparece na interface ou nos registros.

## Registro seguro de execução

A aplicação grava metadados em:

- `/persistent/execucoes.json` no container;
- `logs/execucoes.json` quando o diretório persistente não está disponível.

Cada registro contém apenas timestamp, evento, status e nome do modelo. O registro não contém texto enviado, resposta, chave, token, endereço pessoal ou conteúdo de credencial.

Os arquivos anteriores de histórico da interface podem conter anotações e respostas e devem ser tratados como dados sensíveis. Use o diretório `/persistent` conforme necessário.

## Versões documentadas

- Python: 3.11 ou superior;
- Docker base: `python:3.11-slim`;
- Streamlit: `1.67.0`;
- Requests: `2.34.2`;
- Ollama: API compatível com `/api/tags` e `/api/chat`.

Para reproduzir o ambiente, sempre use um ambiente virtual novo e instale somente `requirements.txt`.

## Validação em ambiente limpo

Uma validação final deve ser feita em um ambiente virtual vazio:

```powershell
python -m venv .venv-clean
.\.venv-clean\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m unittest -v
python -m py_compile main.py app.py execution_log.py test_main.py
```

Sem acesso ao LLM, use os testes simulados. Para demonstrar o funcionamento real, configure `OLLAMA_HOST` e `OLLAMA_MODEL` e execute `python main.py` com uma entrada válida.

## Registro de validação

- Ambiente usado no desenvolvimento: Windows com Python 3.14 para o editor e Docker com Python 3.11.
- Resultado dos testes locais: os testes do módulo `test_main.py` passaram sem chamada externa.
- Problema observado durante a evolução intermediária: a versão inicial do repositório não continha o fluxo CLI `main.py` e o projeto precisava ser integrado ao histórico remoto existente.
- Correção: o histórico foi integrado com uma pull request/merge, o fluxo foi separado em funções e o arquivo foi publicado na branch principal.
