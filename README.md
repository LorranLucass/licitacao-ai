# LicitaPDF

Sistema interno para análise automatizada de editais de licitação.
Recebe o PDF do edital, extrai os dados relevantes com IA e cruza os
itens com a tabela de produtos de referência, gerando um bloco de
notas pronto para a proposta.

## Como funciona

1. Upload do edital em PDF pela interface web.
2. `services/pdf_reader.py` extrai o texto do documento.
3. `services/ai_extractor.py` envia o texto para a IA e retorna os
   dados estruturados (órgão, prazos, itens, exigências etc.).
4. `services/item_matcher.py` cruza os itens do edital com a tabela
   de produtos (`dados/produtos.xlsx`) e mantém só os compatíveis.
5. `services/bloco_notas.py` gera o `saida/bloco_notas.txt` final.

## Configuração

1. Crie um arquivo `.env` na raiz (use `.env.example` como base) com:
   ```
   OPENAI_API_KEY=sua_chave_aqui
   ```
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Rode a aplicação:
   ```
   python app.py
   ```
4. Acesse `http://127.0.0.1:5000`.

Por padrão o servidor roda com `debug` desligado. Para ligar em
ambiente de desenvolvimento, defina `FLASK_DEBUG=1` no `.env`.

## Identidade visual

Paleta, tipografia e arquivos da logo estão em `brand/GUIA_DE_MARCA.md`.
