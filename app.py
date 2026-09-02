import os
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv

from flask import (
    Flask,
    render_template,
    request,
    send_file,
)

from werkzeug.utils import secure_filename

from services.pdf_reader import extrair_texto_pdf
from services.ai_extractor import extrair_dados_com_ia
from services.item_matcher import filtrar_itens
from services.bloco_notas import gerar_bloco_notas
from services.trello_texto import gerar_texto_trello
from services.proposta_word import gerar_proposta_word


# ============================================================
# CONFIGURAÇÃO
# ============================================================

load_dotenv()

DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"


app = Flask(
    __name__,
    template_folder="interface/templates",
    static_folder="interface/static",
)


# ============================================================
# PASTAS TEMPORÁRIAS
# ============================================================

if os.name == "nt":
    PASTA_TEMP = Path(
        os.getenv("TEMP", "/tmp")
    )
else:
    PASTA_TEMP = Path("/tmp")


PASTA_SAIDA = (
    PASTA_TEMP /
    "licitapdf_saida"
)

PASTA_EDITAIS = (
    PASTA_TEMP /
    "licitapdf_editais"
)


PASTA_SAIDA.mkdir(
    parents=True,
    exist_ok=True
)

PASTA_EDITAIS.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# CAMINHO DO MODELO WORD
# ============================================================

PASTA_PROJETO = (
    Path(__file__).resolve().parent
)

CAMINHO_TEMPLATE_WORD = (
    PASTA_PROJETO /
    "interface" /
    "modelos" /
    "proposta.docx"
)


# ============================================================
# DADOS DA ÚLTIMA PROPOSTA
# ============================================================

dados_ultima_proposta = {}
nome_ultimo_arquivo = ""


# ============================================================
# PÁGINA INICIAL
# ============================================================

@app.route("/")
def inicio():

    return render_template(
        "index.html"
    )


# ============================================================
# ANALISAR EDITAL
# ============================================================

@app.route(
    "/analisar",
    methods=["POST"]
)
def analisar():

    global dados_ultima_proposta
    global nome_ultimo_arquivo

    try:

        # ----------------------------------------------------
        # RECEBER ARQUIVO
        # ----------------------------------------------------

        arquivo = request.files.get(
            "arquivo"
        )

        if not arquivo:

            return render_template(
                "erro.html",
                erro=(
                    "Nenhum arquivo PDF "
                    "foi selecionado."
                )
            )

        if not arquivo.filename:

            return render_template(
                "erro.html",
                erro=(
                    "O arquivo selecionado "
                    "não possui nome."
                )
            )


        # ----------------------------------------------------
        # VALIDAR NOME
        # ----------------------------------------------------

        nome_arquivo = secure_filename(
            arquivo.filename
        )

        if not nome_arquivo:

            return render_template(
                "erro.html",
                erro=(
                    "Nome de arquivo inválido."
                )
            )


        # ----------------------------------------------------
        # VALIDAR EXTENSÃO
        # ----------------------------------------------------

        if not nome_arquivo.lower().endswith(
            ".pdf"
        ):

            return render_template(
                "erro.html",
                erro=(
                    "O arquivo precisa estar "
                    "no formato PDF."
                )
            )


        # ----------------------------------------------------
        # SALVAR PDF
        # ----------------------------------------------------

        caminho_pdf = (
            PASTA_EDITAIS /
            nome_arquivo
        )

        arquivo.save(
            str(caminho_pdf)
        )


        # ----------------------------------------------------
        # CABEÇALHO
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("LICITA PDF")
        print("=" * 60)
        print()


        # ----------------------------------------------------
        # LER PDF
        # ----------------------------------------------------

        print(
            "Lendo edital..."
        )

        texto = extrair_texto_pdf(
            str(caminho_pdf)
        )

        if not texto or not texto.strip():

            return render_template(
                "erro.html",
                erro=(
                    "Não foi possível extrair "
                    "texto do PDF."
                )
            )


        print(
            "PDF lido com sucesso."
        )


        # ----------------------------------------------------
        # IA
        # ----------------------------------------------------

        print(
            "Enviando edital "
            "para análise da IA..."
        )

        dados = extrair_dados_com_ia(
            texto
        )

        if not isinstance(
            dados,
            dict
        ):

            raise ValueError(
                "A IA não retornou os dados "
                "em formato válido."
            )


        print(
            "Dados extraídos com sucesso."
        )


        # ----------------------------------------------------
        # FILTRO DELTA
        # ----------------------------------------------------

        print(
            "Procurando produtos "
            "compatíveis na tabela DELTA..."
        )

        dados = filtrar_itens(
            dados
        )

        if not isinstance(
            dados,
            dict
        ):

            raise ValueError(
                "O filtro de itens "
                "não retornou dados válidos."
            )


        # ----------------------------------------------------
        # MOSTRAR ITENS
        # ----------------------------------------------------

        print()
        print(
            "ITENS ENCONTRADOS "
            "NA TABELA DELTA:"
        )
        print(
            "-" * 50
        )


        for item in dados.get(
            "itens",
            []
        ):

            print(
                f"Item: "
                f"{item.get('item', '')}"
            )

            print(
                f"Produto: "
                f"{item.get('produto_tabela', '')}"
            )

            print(
                f"Marca: "
                f"{item.get('marca_tabela', '')}"
            )

            print(
                f"Modelo: "
                f"{item.get('modelo', '')}"
            )

            print(
                f"Custo: "
                f"{item.get('custo', '')}"
            )

            print(
                f"Mínimo Feirão: "
                f"{item.get('minimo_feirao', '')}"
            )

            print(
                "-" * 50
            )


        # ----------------------------------------------------
        # GUARDAR DADOS
        # ----------------------------------------------------

        dados_ultima_proposta = dados
        nome_ultimo_arquivo = nome_arquivo


        # ====================================================
        # BLOCO DE NOTAS
        # ====================================================

        print(
            "Gerando bloco de notas..."
        )

        caminho_bloco = (
            PASTA_SAIDA /
            "bloco_notas.txt"
        )


        texto_bloco = gerar_bloco_notas(
            dados,
            str(caminho_bloco)
        )


        if not texto_bloco:

            if caminho_bloco.exists():

                texto_bloco = (
                    caminho_bloco
                    .read_text(
                        encoding="utf-8"
                    )
                )

            else:

                texto_bloco = ""


        print(
            "Bloco de notas "
            "gerado com sucesso!"
        )


        # ====================================================
        # TRELLO
        # ====================================================

        print(
            "Gerando texto para o Trello..."
        )

        texto_trello = gerar_texto_trello(
            dados
        )


        if texto_trello is None:

            texto_trello = ""


        caminho_trello = (
            PASTA_SAIDA /
            "texto_trello.txt"
        )


        caminho_trello.write_text(
            str(texto_trello),
            encoding="utf-8"
        )


        print(
            "Texto para o Trello "
            "gerado com sucesso!"
        )


        # ====================================================
        # PROPOSTA WORD
        # ====================================================
        # A proposta Word NÃO é gerada automaticamente aqui.
        # Ela só é criada quando o usuário clica no botão
        # "Gerar proposta Word" na tela de resultado, que
        # aciona a rota /gerar-proposta.

        proposta_disponivel = False

        # ====================================================
        # RESULTADO
        # ====================================================

        print()
        print(
            "=" * 60
        )

        print(
            "ANÁLISE CONCLUÍDA."
        )

        print(
            "=" * 60
        )

        print()


        return render_template(
            "resultado.html",

            dados=dados,

            nome_arquivo=(
                nome_arquivo
            ),

            texto_bloco=(
                texto_bloco
            ),

            texto_trello=(
                texto_trello
            ),

            proposta_disponivel=(
                proposta_disponivel
            ),
        )


    except Exception as erro:

        print()
        print(
            "=" * 60
        )

        print(
            "ERRO DURANTE A ANÁLISE:"
        )

        print(
            repr(erro)
        )

        print(
            "=" * 60
        )

        print()


        return render_template(
            "erro.html",
            erro=str(erro)
        )


# ============================================================
# DOWNLOAD DO BLOCO DE NOTAS
# ============================================================

@app.route(
    "/download",
    methods=["POST"]
)
def download():

    texto = request.form.get(
        "texto_bloco",
        ""
    )


    if not texto:

        return render_template(
            "erro.html",
            erro=(
                "O bloco de notas "
                "não possui conteúdo."
            )
        ), 404


    arquivo = BytesIO(
        texto.encode("utf-8")
    )

    arquivo.seek(0)


    return send_file(
        arquivo,
        as_attachment=True,
        download_name="bloco_notas.txt",
        mimetype=(
            "text/plain; charset=utf-8"
        ),
    )


# ============================================================
# DOWNLOAD DO TRELLO
# ============================================================

@app.route(
    "/download-trello",
    methods=["POST"]
)
def download_trello():

    texto = request.form.get(
        "texto_trello",
        ""
    )


    if not texto:

        return render_template(
            "erro.html",
            erro=(
                "O texto para o Trello "
                "não possui conteúdo."
            )
        ), 404


    arquivo = BytesIO(
        texto.encode("utf-8")
    )

    arquivo.seek(0)


    return send_file(
        arquivo,
        as_attachment=True,
        download_name="texto_trello.txt",
        mimetype=(
            "text/plain; charset=utf-8"
        ),
    )


# ============================================================
# GERAR PROPOSTA WORD (SOB DEMANDA)
# ============================================================
# Só roda quando o usuário clica no botão "Gerar proposta
# Word" na tela de resultado — não durante a análise do
# edital. Reaproveita os dados da última análise (guardados
# em memória) para preencher o modelo Word.

@app.route(
    "/gerar-proposta",
    methods=["POST"]
)
def gerar_proposta():

    global dados_ultima_proposta

    dados = dados_ultima_proposta

    if not dados:

        return render_template(
            "erro.html",
            erro=(
                "Nenhuma análise em andamento. "
                "Analise um edital primeiro."
            )
        )

    # --------------------------------------------------------
    # RECONSTRUIR BLOCO DE NOTAS E TRELLO
    # --------------------------------------------------------
    # Precisam existir de novo para reexibir a tela de
    # resultado completa (não é uma chamada de IA, só
    # remonta o texto a partir dos dados já extraídos —
    # rápido e sem custo).

    caminho_bloco = (
        PASTA_SAIDA /
        "bloco_notas.txt"
    )

    texto_bloco = gerar_bloco_notas(
        dados,
        str(caminho_bloco)
    ) or ""

    texto_trello = gerar_texto_trello(
        dados
    ) or ""

    # --------------------------------------------------------
    # GERAR PROPOSTA WORD
    # --------------------------------------------------------

    caminho_proposta = (
        PASTA_SAIDA /
        "proposta_preenchida.docx"
    )

    proposta_disponivel = False
    erro_proposta = None

    if not CAMINHO_TEMPLATE_WORD.exists():

        erro_proposta = (
            "Não foi possível gerar a proposta Word: "
            "o modelo não foi encontrado no servidor."
        )

        print(
            "ERRO: modelo Word não encontrado em",
            CAMINHO_TEMPLATE_WORD
        )

    else:

        if caminho_proposta.exists():

            try:

                caminho_proposta.unlink()

            except Exception as erro:

                print(
                    "Não foi possível remover "
                    "proposta anterior:",
                    repr(erro)
                )

        try:

            gerar_proposta_word(
                dados=dados,
                caminho_template=(
                    CAMINHO_TEMPLATE_WORD
                ),
                caminho_saida=(
                    caminho_proposta
                ),
            )

            if (
                caminho_proposta.exists()
                and caminho_proposta.stat().st_size > 0
            ):

                proposta_disponivel = True

                print(
                    "PROPOSTA WORD GERADA COM SUCESSO!"
                )

            else:

                erro_proposta = (
                    "Não foi possível gerar a "
                    "proposta Word."
                )

                print(
                    "ERRO: o arquivo Word foi "
                    "gerado vazio ou não foi criado."
                )

        except Exception as erro_word:

            # Não derruba a análise: a tela de resultado
            # continua sendo mostrada normalmente, só com
            # o aviso de erro na proposta.

            erro_proposta = (
                "Não foi possível gerar a "
                "proposta Word."
            )

            print()
            print(
                "ERRO AO GERAR PROPOSTA WORD:"
            )

            print(
                repr(erro_word)
            )

            print()

    return render_template(
        "resultado.html",

        dados=dados,

        nome_arquivo=(
            nome_ultimo_arquivo
        ),

        texto_bloco=(
            texto_bloco
        ),

        texto_trello=(
            texto_trello
        ),

        proposta_disponivel=(
            proposta_disponivel
        ),

        erro_proposta=(
            erro_proposta
        ),
    )


# ============================================================
# DOWNLOAD DA PROPOSTA WORD
# ============================================================

@app.route(
    "/download-proposta",
    methods=["GET"]
)
def download_proposta():

    caminho_proposta = (
        PASTA_SAIDA /
        "proposta_preenchida.docx"
    )


    if not caminho_proposta.exists():

        return render_template(
            "erro.html",
            erro=(
                "A proposta Word ainda "
                "não foi gerada."
            )
        ), 404


    tamanho = (
        caminho_proposta.stat()
        .st_size
    )


    if tamanho <= 0:

        return render_template(
            "erro.html",
            erro=(
                "A proposta Word foi "
                "gerada vazia."
            )
        ), 500


    return send_file(
        str(caminho_proposta),

        as_attachment=True,

        download_name=(
            "proposta_preenchida.docx"
        ),

        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
    )


# ============================================================
# EXECUTAR LOCALMENTE
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=DEBUG
    )