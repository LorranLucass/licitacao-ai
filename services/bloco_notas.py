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


def extrair_numero_processo(texto):
    """
    Extrai somente o número/ano de um texto de modalidade.

    Exemplo:

    "PREGÃO ELETRÔNICO Nº 010/2026"

    Resultado:

    "010/2026"

    Se não achar o padrão NÚMERO/ANO, remove palavras comuns
    da modalidade e devolve o que sobrar.
    """

    if not texto:
        return ""

    texto = str(texto).strip()

    resultado = re.search(
        r"(\d{1,5}\s*/\s*\d{2,4})",
        texto
    )

    if resultado:
        return resultado.group(1).replace(" ", "")

    texto_limpo = texto.upper()

    for termo in [
        "PREGÃO ELETRÔNICO",
        "PREGAO ELETRONICO",
        "PREGÃO PRESENCIAL",
        "PREGAO PRESENCIAL",
        "PREGÃO",
        "PREGAO",
        "DISPENSA ELETRÔNICA",
        "DISPENSA ELETRONICA",
        "DISPENSA",
        "CONCORRÊNCIA",
        "CONCORRENCIA",
        "TOMADA DE PREÇOS",
        "TOMADA DE PRECOS",
        "CONVITE",
        "Nº",
        "N°",
        "NO",
        "N.",
    ]:
        texto_limpo = texto_limpo.replace(termo, "")

    return texto_limpo.strip(" :.-–—")


def formatar_pregao_dispensa(dados):
    """
    Monta o rótulo "Pregão: N" ou "Dispensa: N" de acordo
    com a modalidade identificada no edital.
    """

    modalidade = str(
        dados.get("modalidade", "")
    ).strip().upper()

    numero = extrair_numero_processo(
        dados.get("pregao_dispensa", "")
    )

    if "DISPENSA" in modalidade:
        rotulo = "Dispensa"

    elif "PREGÃO" in modalidade or "PREGAO" in modalidade:
        rotulo = "Pregão"

    elif "DISPENSA" in str(
        dados.get("pregao_dispensa", "")
    ).upper():
        rotulo = "Dispensa"

    else:
        # Padrão mais comum quando a modalidade não veio
        # claramente identificada.
        rotulo = "Pregão"

    if not numero:
        return f"{rotulo}: "

    return f"{rotulo}: {numero}"


def formatar_data_hora_sessao(dados):
    """
    Junta data + horário da sessão em um único texto:

    "04/09/2026 às 15:00"

    Aceita horário em formatos como "15h00min", "15h", "15:00".
    """

    data = str(
        dados.get("data_sessao", "")
    ).strip()

    horario_bruto = str(
        dados.get("horario_sessao", "")
    ).strip()

    horario = ""

    if horario_bruto:

        resultado = re.search(
            r"(\d{1,2})\s*[hH:]\s*(\d{2})?",
            horario_bruto
        )

        if resultado:

            hora = int(resultado.group(1))
            minuto = int(resultado.group(2) or 0)

            horario = f"{hora:02d}:{minuto:02d}"

        else:
            horario = horario_bruto

    if data and horario:
        return f"{data} às {horario}"

    return data or horario or "CONFORME EDITAL"


def calcular_valor_total_proposta(itens):
    """
    Calcula o valor total da proposta a partir dos itens,
    usando a mesma regra do bloco de notas:

    - se o item tem valor estimado no edital, usa esse valor
      (ou valor_unitário × quantidade, se não vier o total);
    - senão, usa custo × 1,60 × quantidade.

    Usada tanto pelo bloco de notas quanto pela proposta Word,
    para os dois nunca mostrarem valores diferentes.
    """

    valor_total_proposta = 0.0

    for item in itens or []:

        quantidade = converter_quantidade(
            item.get("quantidade", 0)
        )

        custo = converter_numero(
            item.get("custo", 0)
        )

        valor_unitario = item.get("valor_unitario")
        valor_total = item.get("valor_total")

        tem_estimado = (
            valor_unitario is not None
            and str(valor_unitario).strip() != ""
        )

        if tem_estimado:

            estimado_unitario = converter_numero(
                valor_unitario
            )

            if (
                valor_total is not None
                and str(valor_total).strip()
            ):
                estimado_total = converter_numero(valor_total)

            else:
                estimado_total = estimado_unitario * quantidade

            valor_total_proposta += estimado_total

        else:

            lancar_total = (custo * 1.60) * quantidade
            valor_total_proposta += lancar_total

    return valor_total_proposta


def gerar_bloco_notas(
    dados: dict,
    caminho_saida: str
):

    linhas = []

    # ==================================================
    # CABEÇALHO
    # ==================================================

    linhas.append(f"{dados.get('orgao', '')}")
    linhas.append(formatar_pregao_dispensa(dados))

    linhas.append(
        f"Processo administrativo: "
        f"{dados.get('processo_administrativo', '')}"
    )

    linhas.append(
        f"Cidade/Estado: "
        f"{dados.get('cidade_estado', '')}"
    )

    linhas.append(
        f"Data da sessão: "
        f"{formatar_data_hora_sessao(dados)}"
    )

    linhas.append("")

    linhas.append(
        f"Modo de disputa: "
        f"{dados.get('modo_disputa', '')}"
    )

    linhas.append("")

    # ==================================================
    # ADESÃO / CARONA
    # ==================================================
    # O valor já vem normalizado em "SIM"/"NÃO" pela
    # extração da IA. Este fallback só cobre o caso de
    # vir algo fora do padrão.

    adesao = str(
        dados.get("adesao_carona", "")
    ).strip().upper()

    if adesao not in ["SIM", "NÃO"]:

        adesao = (
            "SIM"
            if adesao in ["S", "SIM"]
            else "NÃO"
            if adesao
            else ""
        )

    linhas.append(
        f"Adesão / Carona: {adesao}"
    )

    linhas.append("")

    linhas.append(
        f"Intervalo / Redução: "
        f"{dados.get('intervalo_reducao', '')}"
    )

    linhas.append("")
    linhas.append("")

    # ==================================================
    # PRAZOS
    # ==================================================

    proposta = dados.get("proposta_validade", "")

    unidade_validade = (
        dados.get("proposta_validade_unidade", "DIAS")
        or "DIAS"
    )

    entrega = dados.get("entrega_fornecimento", "")
    pagamento = dados.get("pagamento", "")

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

    linhas.append("PRAZOS")

    linhas.append(
        f"Validade da proposta: {proposta}"
        + (
            ""
            if proposta == "CONFORME EDITAL"
            else f" {unidade_validade}"
        )
    )

    linhas.append(
        f"Entrega: {entrega}"
        + (
            ""
            if entrega == "CONFORME EDITAL"
            else " DIAS"
        )
    )

    linhas.append(
        f"Pagamento: {pagamento}"
        + (
            ""
            if pagamento == "CONFORME EDITAL"
            else " DIAS"
        )
    )

    linhas.append("")
    linhas.append("")

    # ==================================================
    # ATENÇÃO
    # ==================================================

    atencao = dados.get("atencao", {})

    if not isinstance(atencao, dict):
        atencao = {}

    linhas.append("ATENÇÃO")

    linhas.append(
        f"Instalação: {atencao.get('instalacao', '')}"
    )

    linhas.append(
        f"Declaração: {atencao.get('declaracao', '')}"
    )

    linhas.append(
        f"Identificação: {atencao.get('identificacao', '')}"
    )

    linhas.append(
        f"Caução: {atencao.get('caucao', '')}"
    )

    linhas.append(
        f"Garantia: {atencao.get('garantia', 'SEM')}"
    )

    garantia_tipos = atencao.get("garantia_tipos", [])

    if not isinstance(garantia_tipos, list):
        garantia_tipos = []

    if len(garantia_tipos) == 1:

        linhas.append(f"Tipo: {garantia_tipos[0]}")

    elif len(garantia_tipos) > 1:

        linhas.append("Tipos:")

        for tipo in garantia_tipos:
            linhas.append(f"- {tipo}")

    linhas.append("")
    linhas.append("")

    # ==================================================
    # ITENS
    # ==================================================

    linhas.append("ITENS")
    linhas.append("")

    valor_total_proposta = 0.0
    valor_custo_total = 0.0

    itens = dados.get("itens", [])

    for indice, item in enumerate(itens):

        produto_tabela = item.get("produto_tabela", "")
        descricao_edital = item.get("descricao", "")

        marca = item.get("marca_tabela", "") or "HQ"
        modelo = item.get("modelo", "")
        fabricante = "BELMICRO"

        quantidade = converter_quantidade(
            item.get("quantidade", 0)
        )

        custo = converter_numero(
            item.get("custo", 0)
        )

        minimo = converter_numero(
            item.get("minimo_feirao", 0)
        )

        valor_unitario = item.get("valor_unitario")
        valor_total = item.get("valor_total")

        tem_estimado = (
            valor_unitario is not None
            and str(valor_unitario).strip() != ""
        )

        # ==============================================
        # ITEM N : PRODUTO
        # ==============================================

        linhas.append(
            f"Item {item.get('item', '')} : {produto_tabela}"
        )

        linhas.append("")

        linhas.append(descricao_edital)

        linhas.append("")
        linhas.append("")

        linhas.append(f"Marca: {marca}")
        linhas.append(f"Modelo: {modelo}")
        linhas.append(f"Fabricante: {fabricante}")

        linhas.append("")

        linhas.append(f"Quantidade: {item.get('quantidade', '')}")

        linhas.append("")
        linhas.append("")

        # ==============================================
        # COM ESTIMADO / SEM ESTIMADO
        # ==============================================

        if tem_estimado:

            estimado_unitario = converter_numero(valor_unitario)

            if valor_total is not None and str(valor_total).strip():
                estimado_total = converter_numero(valor_total)
            else:
                estimado_total = estimado_unitario * quantidade

            custo_total = custo * quantidade
            minimo_total = minimo * quantidade

            linhas.append("COM ESTIMADO:")

            linhas.append(
                f">>>> ESTIMADO UNITÁRIO: "
                f"{formatar_moeda(estimado_unitario)}"
            )

            linhas.append(
                f">>>> ESTIMADO TOTAL: "
                f"{formatar_moeda(estimado_total)}"
            )

            linhas.append(
                f">>>> CUSTO: {formatar_moeda(custo)}"
            )

            linhas.append(
                f">>>> CUSTO TOTAL: {formatar_moeda(custo_total)}"
            )

            linhas.append(
                f">>>> MÍNIMO UNITÁRIO: {formatar_moeda(minimo)}"
            )

            linhas.append(
                f">>>> MÍNIMO TOTAL: {formatar_moeda(minimo_total)}"
            )

            valor_total_proposta += estimado_total

        else:

            custo_total = custo * quantidade
            minimo_total = minimo * quantidade

            lancar_unitario = custo * 1.60
            lancar_total = lancar_unitario * quantidade

            linhas.append("SEM ESTIMADO:")

            linhas.append(
                f">>>> CUSTO: {formatar_moeda(custo)}"
            )

            linhas.append(
                f">>>> CUSTO TOTAL: {formatar_moeda(custo_total)}"
            )

            linhas.append(
                f">>>> MÍNIMO UNITÁRIO: {formatar_moeda(minimo)}"
            )

            linhas.append(
                f">>>> MÍNIMO TOTAL: {formatar_moeda(minimo_total)}"
            )

            linhas.append(
                f">>>> LANÇAR UNITÁRIO: "
                f"{formatar_moeda(lancar_unitario)}"
            )

            linhas.append(
                f">>>> LANÇAR TOTAL: {formatar_moeda(lancar_total)}"
            )

            valor_total_proposta += lancar_total

        valor_custo_total += custo * quantidade

        # Separador entre um item e o próximo (mesma
        # espaçamento usado entre as outras seções).
        if indice < len(itens) - 1:
            linhas.append("")
            linhas.append("")

    # ==================================================
    # TOTAIS
    # ==================================================

    linhas.append("")
    linhas.append("")

    linhas.append(
        f"Valor total da proposta: "
        f"{formatar_moeda(valor_total_proposta)}"
    )

    linhas.append("")

    linhas.append(
        f"Valor custo total: "
        f"{formatar_moeda(valor_custo_total)}"
    )

    # ==================================================
    # SALVAR
    # ==================================================

    texto_final = "\n".join(linhas)

    arquivo = Path(caminho_saida)

    arquivo.parent.mkdir(parents=True, exist_ok=True)

    arquivo.write_text(texto_final, encoding="utf-8")

    return texto_final
