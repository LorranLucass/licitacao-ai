# services/trello_texto.py

from services.bloco_notas import (
    formatar_moeda,
    converter_numero,
    converter_quantidade,
)


# ============================================================
# TEXTO PARA O TRELLO
# ============================================================
# Gera o texto pronto para colar na descrição de um card do
# Trello, no formato:
#
#   - MODO DE DISPUTA: ...
#   - PORTAL: ...
#   - MODALIDADE: ...
#   - Nº DO PROCESSO ADMINISTRATIVO: ...
#   - PRODUTO:
#   - ITEM N: descrição
#     QUANTIDADE: X
#   - DATA DE ABERTURA: DD/MM/AAAA - HH:MM
#   - PRAZO DE ENTREGA: N DIAS
#   - VALIDADE: N MESES.
#   - PAGAMENTO: N DIAS
#   - VALOR PROPOSTA CADASTRADA: R$ ...
#   - VALOR TOTAL DO CUSTO: R$ ...
#
# Cada linha começa com "- " para que o Trello renderize como
# lista com marcadores ao colar na descrição do card.
# ============================================================

def gerar_texto_trello(dados: dict) -> str:

    linhas = []

    # ============================================================
    # MODO DE DISPUTA / PORTAL / MODALIDADE / PROCESSO
    # ============================================================

    linhas.append(
        f"- MODO DE DISPUTA: {dados.get('modo_disputa', '')}"
    )

    linhas.append(
        f"- PORTAL: {dados.get('portal', '')}"
    )

    linhas.append(
        f"- MODALIDADE: {dados.get('modalidade', '')}"
    )

    linhas.append(
        f"- Nº DO PROCESSO ADMINISTRATIVO: "
        f"{dados.get('processo_administrativo', '')}"
    )

    # ============================================================
    # ITENS
    # ============================================================

    linhas.append("- PRODUTO:")

    itens = dados.get("itens", [])

    valor_total_proposta = 0.0
    valor_custo_total = 0.0

    for item in itens:

        quantidade_bruta = item.get("quantidade", "")
        quantidade = converter_quantidade(quantidade_bruta)

        custo = converter_numero(item.get("custo", 0))
        valor_unitario = item.get("valor_unitario")

        tem_estimado = (
            valor_unitario is not None
            and str(valor_unitario).strip() != ""
        )

        if tem_estimado:
            valor_referencia_unitario = converter_numero(valor_unitario)
        else:
            valor_referencia_unitario = custo * 1.60

        valor_total_proposta += valor_referencia_unitario * quantidade
        valor_custo_total += custo * quantidade

        linhas.append(
            f"- ITEM {item.get('item', '')}: "
            f"{item.get('descricao', '')}"
        )

        linhas.append(
            f"  QUANTIDADE: {quantidade_bruta or quantidade}"
        )

    # ============================================================
    # DATA DE ABERTURA
    # ============================================================

    data_sessao = dados.get("data_sessao", "").strip()
    horario_sessao = dados.get("horario_sessao", "").strip()

    if data_sessao and horario_sessao:
        data_abertura = f"{data_sessao} - {horario_sessao}"
    else:
        data_abertura = data_sessao or horario_sessao or ""

    linhas.append(
        f"- DATA DE ABERTURA: {data_abertura}"
    )

    # ============================================================
    # PRAZO DE ENTREGA
    # ============================================================

    entrega = dados.get("entrega_fornecimento", "").strip()

    linhas.append(
        "- PRAZO DE ENTREGA: "
        + (
            f"{entrega} DIAS"
            if entrega
            else "CONFORME EDITAL"
        )
    )

    # ============================================================
    # VALIDADE
    # ============================================================

    validade = dados.get("proposta_validade", "").strip()
    unidade_validade = (
        dados.get("proposta_validade_unidade", "DIAS")
        or "DIAS"
    )

    linhas.append(
        "- VALIDADE: "
        + (
            f"{validade} {unidade_validade}."
            if validade
            else "CONFORME EDITAL."
        )
    )

    # ============================================================
    # PAGAMENTO
    # ============================================================

    pagamento = dados.get("pagamento", "").strip()

    linhas.append(
        "- PAGAMENTO: "
        + (
            f"{pagamento} DIAS"
            if pagamento
            else "CONFORME EDITAL"
        )
    )

    # ============================================================
    # VALORES TOTAIS
    # ============================================================

    linhas.append(
        f"- VALOR PROPOSTA CADASTRADA: "
        f"{formatar_moeda(valor_total_proposta)}"
    )

    linhas.append(
        f"- VALOR TOTAL DO CUSTO: "
        f"{formatar_moeda(valor_custo_total)}"
    )

    return "\n".join(linhas)
