# Identidade visual — LicitaPDF

## Conceito
O produto processa documentos oficiais (editais) que, no mundo real,
recebem carimbo/selo de aprovação. Esse é o elemento central da marca:
um documento com uma dobra + um selo pontilhado de "compatível".

## Paleta

| Uso                        | Cor       | Hex       |
|-----------------------------|-----------|-----------|
| Tinta (texto, fundo escuro) | Ink       | `#101826` |
| Papel (fundo claro)         | Paper     | `#F4F5F1` |
| Cartão / superfície         | Paper raised | `#FFFFFF` |
| Linhas / bordas             | Line      | `#DDE0D8` |
| Selo oficial / destaque     | Carmim    | `#A02334` |
| Selo "compatível" / sucesso | Verde     | `#2F6B4F` |

## Tipografia

- **Títulos de seção:** Source Serif 4 (peso 700) — dá o tom institucional.
- **Textos e interface:** IBM Plex Sans.
- **Dados, códigos, valores, rótulos:** IBM Plex Mono — remete a formulário/planilha.

Carregadas via Google Fonts nos templates (`base.html`).

## Arquivos

- `logo.svg` — versão completa (marca + nome), para cabeçalhos, propostas, apresentações.
- `marca.svg` — só o símbolo, já com fundo (quadrado arredondado), usado como favicon.
- A marca também está inline no `interface/templates/base.html` (topbar), pra não
  depender de requisição extra e herdar as cores via CSS.

## Uso

- Manter sempre respiro ao redor da logo (não colar em bordas de outros elementos).
- Sobre fundo escuro (`--ink`), usar a versão com o documento em papel claro (já é o padrão do arquivo).
- Não recolorir o selo carmim — ele é o elemento de identidade do produto.
- Se precisar de PNG/ICO (para favicon legado ou Word/PowerPoint), converta o SVG em um
  site como realfavicongenerator.net ou abra em um editor vetorial e exporte.
