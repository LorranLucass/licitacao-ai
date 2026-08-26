from pathlib import Path
import re


def formatar_moeda(valor):
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        valor = 0.0

    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def converter_numero(valor):
    if valor is None:
        return 0.0

    try:
        texto = str(valor).replace("R$", "").strip()

        if "," in texto:
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")

        return float(texto)

    except (TypeError, ValueError):
        return 0.0


def converter_quantidade(valor):
    try:
        return int(
            float(
                str(valor)
                .replace(".", "")
                .replace(",", ".")
            )
        )

    except (TypeError, ValueError):
        return 0


def extrair_modelo(produto):
    """
    Extrai somente o modelo final do produto.

    Exemplo:

    MONITOR 24" GAMER LED FULL HD HQ - 24HQ-LED

    Resultado:

    HQ - 24HQ-LED
    """

    if not produto:
        return ""

    texto = str(produto).strip()

    resultado = re.search(
        r"(HQ\s*-\s*.+)$",
        texto,
        re.IGNORECASE
    )

    if resultado:
        return resultado.group(1).strip()

    return texto


def gerar_bloco_notas(
    dados: dict,
    caminho_saida: str
):

    linhas = []

    # ==================================================
    # CABEÇALHO
    # ==================================================

    linhas.append("================================")
    linhas.append("LICITAÇÃO")
    linhas.append("================================")
    linhas.append("")

    linhas.append(
        f"ORGÃO: {dados.get('orgao', '')}"
    )

    linhas.append(
        f"PREGÃO/DISPENSA: "
        f"{dados.get('pregao_dispensa', '')}"
    )

    linhas.append(
        f"UASG (COMPRAS NET): "
        f"{dados.get('uasg', '')}"
    )

    linhas.append(
        f"PROC. ADM: "
        f"{dados.get('processo_administrativo', '')}"
    )

    linhas.append(
        f"HORÁRIO DA SESSÃO: "
        f"{dados.get('horario_sessao', '')}"
    )

    linhas.append(
        f"CIDADE/ESTADO: "
        f"{dados.get('cidade_estado', '')}"
    )

    linhas.append("")

    linhas.append(
        f"MODO DE DISPUTA: "
        f"{dados.get('modo_disputa', '')}"
    )

    linhas.append("")

    # ==================================================
    # ADESÃO / CARONA
    # ==================================================

    adesao = dados.get(
        "adesao_carona",
        ""
    )

    texto_adesao = str(
        adesao
    ).strip().lower()

    if texto_adesao in [
        "sim",
        "s"
    ]:

        adesao_saida = "SIM"

    elif texto_adesao in [
        "não",
        "nao",
        "n"
    ]:

        adesao_saida = "NÃO"

    else:

        adesao_saida = adesao

    linhas.append(
        f"ADESÃO/CARONA - {adesao_saida}"
    )

    linhas.append("")

    # ==================================================
    # PRAZOS
    # ==================================================

    proposta = dados.get(
        "proposta_validade",
        ""
    )

    unidade_validade = dados.get(
        "proposta_validade_unidade",
        "DIAS"
    ) or "DIAS"

    entrega = dados.get(
        "entrega_fornecimento",
        ""
    )

    pagamento = dados.get(
        "pagamento",
        ""
    )

    proposta = (
        proposta
        if str(proposta).strip()
        else "CONFORME EDITAL"
    )

    entrega = (
        entrega
        if str(entrega).strip()
        else "CONFORME EDITAL"
    )

    pagamento = (
        pagamento
        if str(pagamento).strip()
        else "CONFORME EDITAL"
    )

    linhas.append(
        f"PROPOSTA/VALIDADE: {proposta}"
        + (
            ""
            if proposta == "CONFORME EDITAL"
            else f" {unidade_validade}"
        )
    )

    linhas.append(
        f"ENTREGA/FORNECIMENTO: {entrega}"
        + (
            ""
            if entrega == "CONFORME EDITAL"
            else " DIAS"
        )
    )

    linhas.append(
        f"PAGAMENTO: {pagamento}"
        + (
            ""
            if pagamento == "CONFORME EDITAL"
            else " DIAS"
        )
    )

    linhas.append("")

    # ==================================================
    # INTERVALO / REDUÇÃO
    # ==================================================

    linhas.append(
        "INTERVALO/REDUÇÃO - "
        f"{dados.get('intervalo_reducao', '')}"
    )

    linhas.append("")

    # ==================================================
    # ATENÇÃO
    # ==================================================

    atencao = dados.get(
        "atencao",
        {}
    )

    if not isinstance(atencao, dict):
        atencao = {}

    linhas.append("ATENÇÃO:")

    linhas.append(
        f"(COM DECLARAÇÃO OU SEM): "
        f"{atencao.get('declaracao', '')}"
    )

    linhas.append(
        f"(COM IDENTIFICAÇÃO OU SEM): "
        f"{atencao.get('identificacao', '')}"
    )

    linhas.append(
        f"(CAUÇÃO): "
        f"{atencao.get('caucao', '')}"
    )

    linhas.append(
        f"(GARANTIA): "
        f"{atencao.get('garantia', '')}"
    )

    linhas.append("")

    # ==================================================
    # ITENS
    # ==================================================

    valor_total_proposta = 0.0
    valor_custo_total = 0.0

    for item in dados.get(
        "itens",
        []
    ):

        quantidade = converter_quantidade(
            item.get(
                "quantidade",
                0
            )
        )

        custo = converter_numero(
            item.get(
                "custo",
                0
            )
        )

        minimo = converter_numero(
            item.get(
                "minimo_feirao",
                0
            )
        )

        valor_unitario = item.get(
            "valor_unitario"
        )

        valor_total = item.get(
            "valor_total"
        )

        tem_estimado = (
            valor_unitario is not None
            and str(
                valor_unitario
            ).strip() != ""
        )

        # ==================================================
        # DADOS DO PRODUTO DELTA
        # ==================================================

        marca = "HQ"

        # Primeiro tenta o novo campo "modelo"
        modelo = item.get(
            "modelo",
            ""
        )

        # Compatibilidade com versão anterior
        if not modelo:

            modelo = item.get(
                "modelo_tabela",
                ""
            )

        # Se ainda não encontrar,
        # extrai do nome completo do produto.
        if not modelo:

            produto = item.get(
                "produto_tabela",
                ""
            )

            modelo = extrair_modelo(
                produto
            )

        fabricante = "BELMICRO"

        # ==================================================
        # ITEM
        # ==================================================

        linhas.append(
            f"ITEM {item.get('item', '')}: "
            f"{item.get('descricao', '')}"
        )

        linhas.append("")

        linhas.append(
            f"QUANTIDADE: "
            f"{item.get('quantidade', '')}"
        )

        linhas.append("")

        linhas.append(
            f"MARCA: {marca}"
        )

        linhas.append(
            f"MODELO: {modelo}"
        )

        linhas.append(
            f"FABRICANTE: {fabricante}"
        )

        linhas.append("")

        # ==================================================
        # COM ESTIMADO
        # ==================================================

        if tem_estimado:

            estimado_unitario = converter_numero(
                valor_unitario
            )

            if (
                valor_total is not None
                and str(
                    valor_total
                ).strip()
            ):

                estimado_total = converter_numero(
                    valor_total
                )

            else:

                estimado_total = (
                    estimado_unitario
                    * quantidade
                )

            linhas.append(
                "COM ESTIMADO:"
            )

            linhas.append("")

            linhas.append(
                f"ESTIMADO UNITÁRIO: "
                f"{formatar_moeda(estimado_unitario)}"
            )

            linhas.append(
                f"ESTIMADO TOTAL: "
                f"{formatar_moeda(estimado_total)}"
            )

            linhas.append(
                f"CUSTO: "
                f"{formatar_moeda(custo)}"
            )

            custo_total = (
                custo
                * quantidade
            )

            linhas.append(
                f"CUSTO TOTAL: "
                f"{formatar_moeda(custo_total)}"
            )

            minimo_total = (
                minimo
                * quantidade
            )

            linhas.append(
                f"MÍNIMO UNITÁRIO: "
                f"{formatar_moeda(minimo)}"
            )

            linhas.append(
                f"MÍNIMO TOTAL: "
                f"{formatar_moeda(minimo_total)}"
            )

            valor_total_proposta += (
                estimado_total
            )

        # ==================================================
        # SEM ESTIMADO
        # ==================================================

        else:

            custo_total = (
                custo
                * quantidade
            )

            minimo_total = (
                minimo
                * quantidade
            )

            # CUSTO + 60%
            lancar_unitario = (
                custo
                * 1.60
            )

            lancar_total = (
                lancar_unitario
                * quantidade
            )

            linhas.append(
                "SEM ESTIMADO:"
            )

            linhas.append("")

            linhas.append(
                f"CUSTO: "
                f"{formatar_moeda(custo)}"
            )

            linhas.append(
                f"CUSTO TOTAL: "
                f"{formatar_moeda(custo_total)}"
            )

            linhas.append(
                f"MÍNIMO UNITÁRIO: "
                f"{formatar_moeda(minimo)}"
            )

            linhas.append(
                f"MÍNIMO TOTAL: "
                f"{formatar_moeda(minimo_total)}"
            )

            linhas.append(
                f"LANÇAR UNITÁRIO: "
                f"{formatar_moeda(lancar_unitario)}"
            )

            linhas.append(
                f"LANÇAR TOTAL: "
                f"{formatar_moeda(lancar_total)}"
            )

            valor_total_proposta += (
                lancar_total
            )

        # ==================================================
        # CUSTO TOTAL GERAL
        # ==================================================

        valor_custo_total += (
            custo
            * quantidade
        )

        linhas.append("")

        linhas.append(
            "--------------------------------"
        )

        linhas.append("")

    # ==================================================
    # TOTAIS
    # ==================================================

    linhas.append(
        f"VALOR TOTAL DA PROPOSTA: "
        f"{formatar_moeda(valor_total_proposta)}"
    )

    linhas.append(
        f"VALOR CUSTO TOTAL: "
        f"{formatar_moeda(valor_custo_total)}"
    )

    # ==================================================
    # SALVAR
    # ==================================================

    texto_final = "\n".join(linhas)

    arquivo = Path(
        caminho_saida
    )

    arquivo.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    arquivo.write_text(
        texto_final,
        encoding="utf-8"
    )

    return texto_final
    