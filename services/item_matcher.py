from pathlib import Path
import re

from openpyxl import load_workbook


ARQUIVO_PRODUTOS = "dados/produtos.xlsx"
ABA_PRODUTOS = "Pelotão DELTA"

TIPOS_PERMITIDOS = {
    "MONITOR",
    "TV",
}


def carregar_produtos(caminho=ARQUIVO_PRODUTOS):
    arquivo = Path(caminho)

    if not arquivo.exists():
        raise FileNotFoundError(
            f"Tabela de produtos não encontrada: {arquivo}"
        )

    workbook = load_workbook(
        arquivo,
        data_only=True
    )

    if ABA_PRODUTOS not in workbook.sheetnames:
        raise ValueError(
            f"A aba '{ABA_PRODUTOS}' não foi encontrada."
        )

    planilha = workbook[ABA_PRODUTOS]

    produtos = []
    marca_atual = ""

    for linha in planilha.iter_rows(
        min_row=2,
        values_only=True
    ):
        marca, produto, custo, minimo_feirao = linha[:4]

        if not produto:
            continue

        produto = str(produto).strip()

        if marca:
            marca_atual = str(marca).strip()

        tipo = identificar_tipo(produto)

        # SOMENTE TV E MONITOR
        if tipo not in TIPOS_PERMITIDOS:
            continue

        produtos.append({
            "marca": marca_atual,
            "produto": produto,
            "custo": custo,
            "minimo_feirao": minimo_feirao,
            "tipo": tipo,
        })

    return produtos


def identificar_tipo(texto):
    if not texto:
        return None

    texto = str(texto).upper().strip()

    if "MONITOR" in texto:
        return "MONITOR"

    if "SMART TV" in texto:
        return "TV"

    if "TELEVISOR" in texto:
        return "TV"

    if re.search(r"\bTV\b", texto):
        return "TV"

    return None


def extrair_tamanho(texto):
    if not texto:
        return None

    texto = str(texto).upper()

    padroes = [
        r'(\d+(?:[.,]\d+)?)\s*["”″]',
        r'(\d+(?:[.,]\d+)?)\s*POLEGADAS?',
    ]

    for padrao in padroes:
        resultado = re.search(
            padrao,
            texto
        )

        if resultado:
            return resultado.group(1).replace(
                ",",
                "."
            )

    return None


def caracteristicas_compativeis(
    descricao_edital,
    produto
):
    edital = str(
        descricao_edital
    ).upper()

    produto_nome = str(
        produto["produto"]
    ).upper()

    # ==============================
    # CÂMERA / WEBCAM
    # ==============================

    exige_camera = any(
        termo in edital
        for termo in [
            "COM CÂMERA",
            "COM CAMERA",
            "WEBCAM",
            "CÂMERA INTEGRADA",
            "CAMERA INTEGRADA",
            "VIDEOCONFERÊNCIA",
            "VIDEOCONFERENCIA",
        ]
    )

    if exige_camera:

        possui_camera = any(
            termo in produto_nome
            for termo in [
                "CÂMERA",
                "CAMERA",
                "WEBCAM",
            ]
        )

        if not possui_camera:
            return False

    # ==============================
    # 4K
    # ==============================

    exige_4k = "4K" in edital

    if exige_4k and "4K" not in produto_nome:
        return False

    # ==============================
    # QLED
    # ==============================

    exige_qled = "QLED" in edital

    if exige_qled and "QLED" not in produto_nome:
        return False

    # ==============================
    # OLED
    # ==============================

    exige_oled = "OLED" in edital

    if exige_oled and "OLED" not in produto_nome:
        return False

    return True


def encontrar_produto(
    descricao_edital,
    produtos
):
    tipo_edital = identificar_tipo(
        descricao_edital
    )

    # NÃO É TV NEM MONITOR
    if tipo_edital not in TIPOS_PERMITIDOS:
        return None

    tamanho_edital = extrair_tamanho(
        descricao_edital
    )

    # Sem tamanho, não arrisca
    if not tamanho_edital:
        return None

    for produto in produtos:

        # Confere o tipo
        if produto["tipo"] != tipo_edital:
            continue

        tamanho_produto = extrair_tamanho(
            produto["produto"]
        )

        # Confere o tamanho
        if tamanho_produto != tamanho_edital:
            continue

        # Confere características
        if not caracteristicas_compativeis(
            descricao_edital,
            produto
        ):
            continue

        resultado = produto.copy()

        resultado["tamanho"] = tamanho_produto

        return resultado

    return None


def filtrar_itens(dados):

    produtos = carregar_produtos()

    itens_encontrados = []

    for item in dados.get(
        "itens",
        []
    ):
        descricao = item.get(
            "descricao",
            ""
        )

        # Identifica se é TV ou monitor
        tipo = identificar_tipo(
            descricao
        )

        # Ignora tudo que não seja TV ou monitor
        if tipo not in TIPOS_PERMITIDOS:
            continue

        produto = encontrar_produto(
            descricao,
            produtos
        )

        # Se não encontrar compatível,
        # simplesmente ignora.
        if not produto:
            continue

        item_filtrado = item.copy()

        item_filtrado[
            "produto_tabela"
        ] = produto["produto"]

        item_filtrado[
            "marca_tabela"
        ] = produto["marca"]

        item_filtrado[
            "custo"
        ] = produto["custo"]

        item_filtrado[
            "minimo_feirao"
        ] = produto["minimo_feirao"]

        item_filtrado[
            "tamanho"
        ] = produto["tamanho"]

        itens_encontrados.append(
            item_filtrado
        )

    dados_filtrados = dados.copy()

    dados_filtrados[
        "itens"
    ] = itens_encontrados

    return dados_filtrados