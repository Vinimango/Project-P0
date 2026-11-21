# Build e deploy no Devel LLM Portal

## 1. Construir a imagem Docker

Execute na raiz deste projeto:

```powershell
docker build -t vinimangooutlookcom/resumo-reunioes:latest .
```

## 2. Exportar a imagem para upload

```powershell
docker save --output vinimangooutlookcom.tar vinimangooutlookcom/resumo-reunioes:latest
```

Verifique o tamanho antes do envio:

```powershell
Get-Item vinimangooutlookcom.tar | Select-Object Name, Length
```

A imagem Docker exportada não deve ultrapassar 1 GB.

## 3. Preencher o Devel LLM Portal

- **Arquivo da imagem:** `vinimangooutlookcom.tar`
- **Porta HTTP interna:** `80`
- **Variável de ambiente:** `OLLAMA_HOST=https://llm-internal.softex:9001`
- **Comando:** deixe o padrão do Dockerfile

## 4. Teste local opcional

```powershell
docker run --rm -p 8080:80 -e OLLAMA_HOST=https://llm-internal.softex:9001 vinimangooutlookcom/resumo-reunioes:latest
```

Acesse `http://localhost:8080`.

## Persistência

A aplicação cria `/persistent/historico.json` automaticamente. No portal, configure o volume persistente apontando para `/persistent` para preservar o histórico entre reinicializações.
