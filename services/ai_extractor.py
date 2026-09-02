import json
import os

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# CONFIGURAÇÃO
# ============================================================

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# ============================================================
# EXTRAÇÃO DOS DADOS DO EDITAL
# ============================================================

def extrair_dados_com_ia(texto_edital: str) -> dict:

    prompt = f"""
Você é um especialista em análise de editais de licitação.

Analise o edital abaixo e extraia as informações solicitadas.

============================================================
REGRAS GERAIS
============================================================

1. Não invente informações.

2. Se uma informação não estiver no edital, retorne "".

3. PAGAMENTO deve conter somente o número de dias.

4. ENTREGA/FORNECIMENTO deve conter somente o número de dias.

5. PROPOSTA/VALIDADE deve conter somente o número (sem
   escrever a unidade dentro do próprio número). A unidade
   (DIAS ou MESES), exatamente como aparece no edital, vai
   no campo separado "proposta_validade_unidade".

6. Se pagamento, entrega ou validade não forem encontrados,
   retorne "".

7. Mantenha os valores monetários como aparecem no edital.

8. Extraia TODOS os itens encontrados.

9. Não descarte itens nesta etapa.

10. O filtro de produtos será feito posteriormente pela
    tabela DELTA.

11. Retorne SOMENTE JSON válido.

12. Não invente UASG.

13. Para cada item, extraia quantidade e valores estimados
    quando existirem.

14. Se NÃO houver valor estimado, deixe:
    "valor_unitario": ""
    "valor_total": ""

============================================================
REGRA PARA ÓRGÃO
============================================================

15. Extraia somente o nome do órgão.

16. Não inclua número de processo, número do pregão ou
    outras informações dentro do campo "orgao".

============================================================
REGRA PARA PREGÃO/DISPENSA
============================================================

17. O campo "pregao_dispensa" deve conter somente a
    identificação da modalidade e do número.

Exemplo correto:

"PREGÃO ELETRÔNICO Nº 010/2026"

Exemplo incorreto:

"PREGÃO ELETRÔNICO Nº 010/2026 - Processo Administrativo
n.º 035/2026"

18. Nunca coloque o processo administrativo dentro de
    "pregao_dispensa".

19. O processo administrativo deve ser colocado somente
    no campo "processo_administrativo".

============================================================
REGRA PARA PROCESSO ADMINISTRATIVO
============================================================

20. Extraia somente o número ou identificação do processo
    administrativo.

Exemplo:

"035/2026"

============================================================
REGRA PARA PORTAL
============================================================

20a. Extraia o nome do portal/site onde o certame é
     realizado (exemplos: AMML, Compras.gov.br, BLL, BNC,
     Licitanet, BBMNET).

20b. Retorne somente o nome do portal, sem link e sem
     explicações.

============================================================
REGRA PARA MODALIDADE
============================================================

20c. Extraia a modalidade do certame (exemplos: PREGÃO,
     DISPENSA, CONCORRÊNCIA, TOMADA DE PREÇOS, CONVITE).

20d. Retorne somente a modalidade, sem o número do processo
     e sem a palavra "ELETRÔNICO" a menos que faça parte do
     nome oficial da modalidade.

============================================================
REGRA PARA DECLARAÇÃO
============================================================

21. Analise o edital e seus anexos quanto às exigências
    relacionadas a declarações.

22. O campo "declaracao" deve aceitar SOMENTE uma destas
    três respostas:

    "COM"
    "SEM"
    "COM OU SEM"

23. Se o edital exigir declaração obrigatória, retorne:

    "COM"

24. Se o edital disser que não há declaração ou que não é
    necessária, retorne:

    "SEM"

25. Se o edital indicar que a participação pode ocorrer
    COM OU SEM determinada declaração, retorne:

    "COM OU SEM"

26. Não escreva o nome da declaração.

27. Não escreva explicações no campo "declaracao".

============================================================
REGRA PARA IDENTIFICAÇÃO
============================================================

28. Analise o edital quanto à necessidade de identificação
    do produto, proposta, concorrente, embalagem, etiqueta
    ou qualquer identificação semelhante.

29. O campo "identificacao" deve aceitar SOMENTE uma destas
    três respostas:

    "COM"
    "SEM"
    "COM OU SEM"

30. Se a identificação for obrigatória, retorne:

    "COM"

31. Se o edital disser que não haverá identificação ou que
    não é necessária, retorne:

    "SEM"

32. Se o edital permitir COM OU SEM identificação, retorne:

    "COM OU SEM"

33. Não escreva explicações no campo "identificacao".

============================================================
REGRA PARA INSTALAÇÃO
============================================================

34. O campo "instalacao" deve indicar somente:

    "SIM"
    ou
    "NÃO"

35. Se o edital exigir instalação, montagem ou serviço de
    instalação, retorne "SIM".

36. Caso contrário, retorne "NÃO".

============================================================
REGRA PARA CAUÇÃO
============================================================

37. O campo "caucao" deve aceitar somente:

    "SIM"
    ou
    "NÃO HAVERÁ"

38. Se o edital disser que não haverá caução, retorne:

    "NÃO HAVERÁ"

39. Se houver exigência de caução, retorne:

    "SIM"

40. Não escreva explicações no campo "caucao".

============================================================
REGRA PARA GARANTIA
============================================================

41. Procure especificamente por estas modalidades de
    garantia no edital e seus anexos:

    - Garantia Contratual
    - Garantia de Execução
    - Garantia On-site

42. NÃO confunda essas modalidades com uma simples garantia
    comercial do produto (ex: "garantia do fabricante de 12
    meses"). Isso NÃO conta como garantia contratual, de
    execução ou on-site.

43. O campo "garantia" deve conter SOMENTE:

    "COM"
    ou
    "SEM"

44. Se o edital exigir uma ou mais dessas modalidades,
    retorne "COM" e liste, em "garantia_tipos", exatamente
    quais delas foram exigidas (usando os nomes acima,
    exatamente como escritos).

45. Se nenhuma dessas modalidades for exigida (mesmo que
    exista garantia comercial do produto), retorne "SEM" e
    "garantia_tipos": [].

Exemplo (com garantia de execução):

"garantia": "COM",
"garantia_tipos": ["Garantia de Execução"]

Exemplo (sem nenhuma das três):

"garantia": "SEM",
"garantia_tipos": []

============================================================
REGRA PARA OBJETO
============================================================

45a. Extraia um resumo objetivo do objeto da licitação
     (o que está sendo contratado/adquirido), em uma frase.

45b. Não copie o texto inteiro do edital.

Exemplo:

"Aquisição de monitores e televisores para uso nas
unidades administrativas do município."

============================================================
REGRA PARA ADESÃO / CARONA
============================================================

45c. O campo "adesao_carona" deve conter SOMENTE:

     "SIM"
     ou
     "NÃO"

45d. Interprete frases do tipo:

     "Será permitida a adesão" -> "SIM"
     "Permitida carona" -> "SIM"
     "Não será permitida adesão" -> "NÃO"
     "Não será permitida carona" -> "NÃO"
     "Não se aplica" -> "NÃO"

45e. Não escreva explicações, apenas "SIM" ou "NÃO".

============================================================
REGRA PARA ITENS
============================================================

51. Extraia todos os itens encontrados no edital.

52. Não descarte itens por tipo de produto.

53. Não descarte itens por tamanho.

54. Não tente escolher produtos da tabela DELTA.

55. A seleção do produto compatível será feita posteriormente
    pelo sistema.

56. Preserve a descrição técnica completa do item.

============================================================
FORMATO OBRIGATÓRIO
============================================================

Retorne exatamente um JSON com esta estrutura:

{{
    "orgao": "",
    "objeto": "",
    "pregao_dispensa": "",
    "portal": "",
    "modalidade": "",
    "uasg": "",
    "processo_administrativo": "",
    "data_sessao": "",
    "horario_sessao": "",
    "cidade_estado": "",

    "modo_disputa": "",

    "adesao_carona": "",

    "proposta_validade": "",
    "proposta_validade_unidade": "",
    "entrega_fornecimento": "",
    "pagamento": "",

    "intervalo_reducao": "",

    "atencao": {{
        "instalacao": "",
        "declaracao": "",
        "identificacao": "",
        "caucao": "",
        "garantia": "",
        "garantia_tipos": []
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

============================================================
EDITAL
============================================================

{texto_edital}
"""

    # ========================================================
    # CHAMADA PARA A OPENAI
    # ========================================================

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
                    "com precisão. "
                    "Nunca invente informações. "
                    "Retorne somente JSON válido."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # ========================================================
    # CONVERTER RESPOSTA PARA DICT
    # ========================================================

    conteudo = resposta.choices[0].message.content

    dados = json.loads(conteudo)

    # ========================================================
    # GARANTIR CAMPOS PRINCIPAIS
    # ========================================================

    campos = [
        "orgao",
        "objeto",
        "pregao_dispensa",
        "portal",
        "modalidade",
        "uasg",
        "processo_administrativo",
        "data_sessao",
        "horario_sessao",
        "cidade_estado",
        "modo_disputa",
        "adesao_carona",
        "proposta_validade",
        "proposta_validade_unidade",
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

    # ========================================================
    # GARANTIR BLOCO ATENÇÃO
    # ========================================================

    if "atencao" not in dados:
        dados["atencao"] = {}

    if not isinstance(dados["atencao"], dict):
        dados["atencao"] = {}

    campos_atencao = [
        "instalacao",
        "declaracao",
        "identificacao",
        "caucao",
        "garantia",
        "garantia_tipos"
    ]

    for campo in campos_atencao:

        if campo == "garantia_tipos" and campo not in dados["atencao"]:
            dados["atencao"][campo] = []
            continue

        if campo not in dados["atencao"]:
            dados["atencao"][campo] = ""

    # ========================================================
    # NORMALIZAR DECLARAÇÃO
    # ========================================================

    declaracao = str(
        dados["atencao"].get("declaracao", "")
    ).strip().upper()

    declaracao = declaracao.replace("NÃO", "NAO")

    if declaracao in [
        "COM",
        "SIM"
    ]:
        dados["atencao"]["declaracao"] = "COM"

    elif declaracao in [
        "SEM",
        "NAO",
        "N"
    ]:
        dados["atencao"]["declaracao"] = "SEM"

    elif declaracao in [
        "COM OU SEM",
        "SIM OU NAO",
        "SIM OU NÃO"
    ]:
        dados["atencao"]["declaracao"] = "COM OU SEM"

    else:
        dados["atencao"]["declaracao"] = ""

    # ========================================================
    # NORMALIZAR IDENTIFICAÇÃO
    # ========================================================

    identificacao = str(
        dados["atencao"].get("identificacao", "")
    ).strip().upper()

    if identificacao in [
        "COM",
        "SIM"
    ]:
        dados["atencao"]["identificacao"] = "COM"

    elif identificacao in [
        "SEM",
        "NAO",
        "NÃO",
        "N"
    ]:
        dados["atencao"]["identificacao"] = "SEM"

    elif identificacao in [
        "COM OU SEM",
        "SIM OU NAO",
        "SIM OU NÃO"
    ]:
        dados["atencao"]["identificacao"] = "COM OU SEM"

    else:
        dados["atencao"]["identificacao"] = ""

    # ========================================================
    # NORMALIZAR INSTALAÇÃO
    # ========================================================

    instalacao = str(
        dados["atencao"].get("instalacao", "")
    ).strip().upper()

    if instalacao in [
        "SIM",
        "S"
    ]:
        dados["atencao"]["instalacao"] = "SIM"

    elif instalacao in [
        "NAO",
        "NÃO",
        "N"
    ]:
        dados["atencao"]["instalacao"] = "NÃO"

    else:
        dados["atencao"]["instalacao"] = ""

    # ========================================================
    # NORMALIZAR CAUÇÃO
    # ========================================================

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
            "NAO EXIGIDA",
            "NÃO HAVERÁ EXIGÊNCIA",
            "NAO HAVERA EXIGENCIA"
        ]
    ):
        dados["atencao"]["caucao"] = "NÃO HAVERÁ"

    elif caucao in [
        "SIM",
        "S"
    ]:
        dados["atencao"]["caucao"] = "SIM"

    elif caucao:
        dados["atencao"]["caucao"] = "SIM"

    else:
        dados["atencao"]["caucao"] = ""

    # ========================================================
    # NORMALIZAR TIPOS DE GARANTIA
    # ========================================================
    # Somente estas três modalidades são reconhecidas. Uma
    # garantia comercial de produto não entra aqui.

    TIPOS_GARANTIA_VALIDOS = [
        "Garantia Contratual",
        "Garantia de Execução",
        "Garantia On-site",
    ]

    tipos_brutos = dados["atencao"].get("garantia_tipos", [])

    if not isinstance(tipos_brutos, list):
        tipos_brutos = [tipos_brutos] if tipos_brutos else []

    tipos_normalizados = []

    for tipo_bruto in tipos_brutos:

        tipo_texto = str(tipo_bruto).strip().upper()

        for tipo_valido in TIPOS_GARANTIA_VALIDOS:

            if tipo_valido.upper() == tipo_texto:

                if tipo_valido not in tipos_normalizados:
                    tipos_normalizados.append(tipo_valido)

                break

    dados["atencao"]["garantia_tipos"] = tipos_normalizados

    # ========================================================
    # NORMALIZAR GARANTIA (COM / SEM)
    # ========================================================

    garantia = str(
        dados["atencao"].get("garantia", "")
    ).strip().upper()

    if garantia in ["COM", "SIM"] or tipos_normalizados:
        dados["atencao"]["garantia"] = "COM"

    else:
        dados["atencao"]["garantia"] = "SEM"

    # Se disser "COM" mas nenhum tipo específico foi
    # identificado, mantém "COM" (o edital exige garantia,
    # mesmo que a modalidade exata não tenha sido reconhecida).

    # ========================================================
    # NORMALIZAR ADESÃO / CARONA
    # ========================================================

    adesao = str(
        dados.get("adesao_carona", "")
    ).strip().upper()

    adesao_sem_acento = (
        adesao
        .replace("Ã", "A")
        .replace("Á", "A")
        .replace("Â", "A")
    )

    if any(
        termo in adesao_sem_acento
        for termo in [
            "NAO SERA PERMITID",
            "NAO PERMITID",
            "NAO SE APLICA",
            "NAO HAVERA",
        ]
    ):
        dados["adesao_carona"] = "NÃO"

    elif any(
        termo in adesao_sem_acento
        for termo in [
            "SERA PERMITID",
            "PERMITID",
            "HAVERA",
        ]
    ):
        dados["adesao_carona"] = "SIM"

    elif adesao_sem_acento in ["SIM", "S"]:
        dados["adesao_carona"] = "SIM"

    elif adesao_sem_acento in ["NAO", "N"]:
        dados["adesao_carona"] = "NÃO"

    else:
        dados["adesao_carona"] = ""

    # ========================================================
    # LIMPAR PREGÃO/DISPENSA
    # ========================================================

    pregao = str(
        dados.get("pregao_dispensa", "")
    ).strip()

    # Remove informações de processo administrativo
    # que eventualmente tenham sido colocadas pela IA.

    marcadores_processo = [
        " - PROCESSO ADMINISTRATIVO",
        " – PROCESSO ADMINISTRATIVO",
        " — PROCESSO ADMINISTRATIVO",
        ", PROCESSO ADMINISTRATIVO",
        " PROCESSO ADMINISTRATIVO"
    ]

    pregao_upper = pregao.upper()

    for marcador in marcadores_processo:

        posicao = pregao_upper.find(marcador)

        if posicao != -1:
            pregao = pregao[:posicao].strip()
            break

    dados["pregao_dispensa"] = pregao

    # ========================================================
    # NORMALIZAR PROCESSO ADMINISTRATIVO
    # ========================================================

    processo = str(
        dados.get("processo_administrativo", "")
    ).strip()

    processo_upper = processo.upper()

    prefixos = [
        "PROCESSO ADMINISTRATIVO",
        "PROC. ADM.",
        "PROC. ADM",
        "PROCESSO ADM.",
        "PROCESSO ADM"
    ]

    for prefixo in prefixos:

        if processo_upper.startswith(prefixo):

            processo = processo[
                len(prefixo):
            ].strip()

            processo = processo.lstrip(
                ":.-–—ºnN "
            )

            break

    dados["processo_administrativo"] = processo

    # ========================================================
    # NORMALIZAR UNIDADE DA VALIDADE DA PROPOSTA
    # ========================================================

    unidade_validade = str(
        dados.get("proposta_validade_unidade", "")
    ).strip().upper()

    unidade_validade = (
        unidade_validade
        .replace("MESES", "MESES")
        .replace("MÊS", "MESES")
        .replace("MES", "MESES")
    )

    if "MES" in unidade_validade:
        dados["proposta_validade_unidade"] = "MESES"

    elif "DIA" in unidade_validade:
        dados["proposta_validade_unidade"] = "DIAS"

    elif dados.get("proposta_validade"):
        # Não veio unidade clara, mas há um número:
        # assume dias, que é o mais comum em editais.
        dados["proposta_validade_unidade"] = "DIAS"

    else:
        dados["proposta_validade_unidade"] = ""

    # ========================================================
    # NORMALIZAR ITENS
    # ========================================================

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

    if not isinstance(
        dados.get("itens"),
        list
    ):
        dados["itens"] = []

    for item in dados["itens"]:

        if not isinstance(item, dict):
            continue

        for campo in campos_item:

            if campo not in item:
                item[campo] = ""

    # ========================================================
    # RETORNO
    # ========================================================

    return dados