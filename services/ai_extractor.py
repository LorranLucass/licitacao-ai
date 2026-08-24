import json
import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def extrair_dados_com_ia(texto_edital: str) -> dict:

    prompt = f"""
Você é um especialista em análise de editais de licitação.

Analise o edital abaixo e extraia as informações solicitadas.

REGRAS IMPORTANTES:

1. Não invente informações.
2. Se uma informação não estiver no edital, retorne "".
3. PAGAMENTO deve conter somente o número de dias.
4. ENTREGA/FORNECIMENTO deve conter somente o número de dias.
5. PROPOSTA/VALIDADE deve conter somente o número de dias.
6. Se pagamento, entrega ou validade não forem encontrados, retorne "".
7. Mantenha os valores monetários como aparecem no edital.
8. Extraia todos os itens encontrados.
9. Não descarte itens nesta etapa.
10. O filtro de produtos será feito posteriormente pela tabela DELTA.
11. Retorne SOMENTE JSON válido.
12. Não invente UASG.
13. Para cada item, extraia quantidade e valores estimados quando existirem.
14. Se NÃO houver valor estimado, deixe "valor_unitario" e
    "valor_total" vazios.

REGRA PARA DECLARAÇÃO:

15. Analise também os anexos e as exigências do edital.
16. Se existir qualquer declaração exigida ou apresentada nos anexos,
    "declaracao" deve ser exatamente "SIM".
17. Se não existir declaração exigida ou apresentada,
    "declaracao" deve ser exatamente "NÃO".
18. O campo "declaracao" deve conter SOMENTE "SIM" ou "NÃO".
19. Nunca escreva o nome ou conteúdo das declarações.

REGRA PARA INSTALAÇÃO:

20. O campo "instalacao" deve indicar somente "SIM" ou "NÃO".
21. Se o edital exigir instalação, montagem ou serviço de instalação,
    retorne "SIM".
22. Caso contrário, retorne "NÃO".

REGRA PARA IDENTIFICAÇÃO:

23. O campo "identificacao" deve indicar somente "SIM" ou "NÃO".
24. Se houver exigência de identificação do produto, etiqueta,
    identificação do concorrente ou semelhante, retorne "SIM".
25. Caso contrário, retorne "NÃO".

REGRA PARA CAUÇÃO:

26. Se o edital disser que não haverá caução, o campo "caucao"
    deve ser exatamente "NÃO HAVERÁ".
27. Se houver exigência de caução, o campo "caucao"
    deve ser exatamente "SIM".
28. O campo "caucao" deve conter SOMENTE "SIM" ou "NÃO HAVERÁ".
29. Nunca escreva explicações ou o texto completo do edital nesse campo.

REGRA PARA GARANTIA:

30. Extraia a informação referente à garantia.
31. Se não houver exigência de garantia, informe isso de forma resumida.
32. Não escreva o texto inteiro do edital.

FORMATO OBRIGATÓRIO:

{{
    "orgao": "",
    "pregao_dispensa": "",
    "uasg": "",
    "processo_administrativo": "",
    "data_sessao": "",
    "horario_sessao": "",
    "cidade_estado": "",

    "modo_disputa": "",

    "adesao_carona": "",

    "proposta_validade": "",
    "entrega_fornecimento": "",
    "pagamento": "",

    "intervalo_reducao": "",

    "atencao": {{
        "instalacao": "",
        "declaracao": "",
        "identificacao": "",
        "caucao": "",
        "garantia": ""
    }},

    "itens": [
        {{
            "lote": "",
            "item": "",
            "codigo_tce": "",
            "codigo_coplan": "",
            "descricao": "",
            "unidade": "",
            "quantidade": "",
            "valor_unitario": "",
            "valor_total": ""
        }}
    ]
}}

EDITAL:

{texto_edital}
"""

    resposta = client.chat.completions.create(
        model="gpt-5-mini",
        response_format={
            "type": "json_object"
        },
        messages=[
            {
                "role": "system",
                "content": (
                    "Você extrai dados de editais de licitação "
                    "com precisão. Nunca invente informações."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    conteudo = resposta.choices[0].message.content

    dados = json.loads(conteudo)

    # ==================================================
    # CAMPOS PRINCIPAIS
    # ==================================================

    campos = [
        "orgao",
        "pregao_dispensa",
        "uasg",
        "processo_administrativo",
        "data_sessao",
        "horario_sessao",
        "cidade_estado",
        "modo_disputa",
        "adesao_carona",
        "proposta_validade",
        "entrega_fornecimento",
        "pagamento",
        "intervalo_reducao",
        "itens"
    ]

    for campo in campos:

        if campo not in dados:

            if campo == "itens":
                dados[campo] = []
            else:
                dados[campo] = ""

    # ==================================================
    # ATENÇÃO
    # ==================================================

    if "atencao" not in dados:
        dados["atencao"] = {}

    campos_atencao = [
        "instalacao",
        "declaracao",
        "identificacao",
        "caucao",
        "garantia"
    ]

    for campo in campos_atencao:

        if campo not in dados["atencao"]:
            dados["atencao"][campo] = ""

    # ==================================================
    # NORMALIZAR DECLARAÇÃO
    # ==================================================

    declaracao = str(
        dados["atencao"].get("declaracao", "")
    ).strip().upper()

    if declaracao in ["SIM", "S"]:
        dados["atencao"]["declaracao"] = "SIM"

    elif declaracao in ["NAO", "NÃO", "N"]:
        dados["atencao"]["declaracao"] = "NÃO"

    else:
        dados["atencao"]["declaracao"] = ""

    # ==================================================
    # NORMALIZAR INSTALAÇÃO
    # ==================================================

    instalacao = str(
        dados["atencao"].get("instalacao", "")
    ).strip().upper()

    if instalacao in ["SIM", "S"]:
        dados["atencao"]["instalacao"] = "SIM"

    elif instalacao in ["NAO", "NÃO", "N"]:
        dados["atencao"]["instalacao"] = "NÃO"

    else:
        dados["atencao"]["instalacao"] = ""

    # ==================================================
    # NORMALIZAR IDENTIFICAÇÃO
    # ==================================================

    identificacao = str(
        dados["atencao"].get("identificacao", "")
    ).strip().upper()

    if identificacao in ["SIM", "S"]:
        dados["atencao"]["identificacao"] = "SIM"

    elif identificacao in ["NAO", "NÃO", "N"]:
        dados["atencao"]["identificacao"] = "NÃO"

    else:
        dados["atencao"]["identificacao"] = ""

    # ==================================================
    # NORMALIZAR CAUÇÃO
    # ==================================================

    caucao = str(
        dados["atencao"].get("caucao", "")
    ).strip().upper()

    if any(
        termo in caucao
        for termo in [
            "NÃO HAVERÁ",
            "NAO HAVERA",
            "NÃO SERÁ EXIGIDA",
            "NAO SERA EXIGIDA",
            "SEM CAUÇÃO",
            "SEM CAUCAO",
            "NÃO EXIGIDA",
            "NAO EXIGIDA"
        ]
    ):
        dados["atencao"]["caucao"] = "NÃO HAVERÁ"

    elif caucao:
        dados["atencao"]["caucao"] = "SIM"

    else:
        dados["atencao"]["caucao"] = ""

    # ==================================================
    # NORMALIZAR GARANTIA
    # ==================================================

    garantia = str(
        dados["atencao"].get("garantia", "")
    ).strip()

    if not garantia:
        dados["atencao"]["garantia"] = "NÃO"

    # ==================================================
    # ITENS
    # ==================================================

    campos_item = [
        "lote",
        "item",
        "codigo_tce",
        "codigo_coplan",
        "descricao",
        "unidade",
        "quantidade",
        "valor_unitario",
        "valor_total"
    ]

    for item in dados.get("itens", []):

        for campo in campos_item:

            if campo not in item:
                item[campo] = ""

    return dados