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
# PASTA TEMPORÁRIA
# ============================================================
#
# O Vercel possui filesystem somente para leitura no projeto.
#
# A única área apropriada para arquivos temporários durante
# a execução da função é /tmp.
#
# Isso também funciona normalmente no Windows/local.
#

if os.name == "nt":
    PASTA_TEMP = Path(os.getenv("TEMP", "/tmp"))
else:
    PASTA_TEMP = Path("/tmp")


PASTA_SAIDA = PASTA_TEMP / "licitapdf_saida"
PASTA_EDITAIS = PASTA_TEMP / "licitapdf_editais"


PASTA_SAIDA.mkdir(
    parents=True,
    exist_ok=True,
)

PASTA_EDITAIS.mkdir(
    parents=True,
    exist_ok=True,
)


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
        # SALVAR PDF TEMPORARIAMENTE
        # ----------------------------------------------------

        caminho_pdf = (
            PASTA_EDITAIS /
            nome_arquivo
        )

        arquivo.save(
            caminho_pdf
        )


        # ----------------------------------------------------
        # LER PDF
        # ----------------------------------------------------

        print()
        print("================================")
        print("LICITA PDF")
        print("================================")
        print()

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


        # ----------------------------------------------------
        # MOSTRAR ITENS NO TERMINAL
        # ----------------------------------------------------

        print()
        print(
            "ITENS ENCONTRADOS "
            "NA TABELA DELTA:"
        )
        print(
            "----------------------------------"
        )

        for item in dados.get(
            "itens",
            []
        ):

            print(
                f"Item {item.get('item')}: "
                f"{item.get('produto_tabela')}"
            )

            print(
                f"Marca: "
                f"{item.get('marca_tabela')}"
            )

            print(
                f"Modelo: "
                f"{item.get('modelo')}"
            )

            print(
                f"Custo: "
                f"{item.get('custo')}"
            )

            print(
                f"Mín. Feirão: "
                f"{item.get('minimo_feirao')}"
            )

            print()


        # ----------------------------------------------------
        # GERAR BLOCO DE NOTAS
        # ----------------------------------------------------

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


        # Caso a função não retorne o texto,
        # tentamos ler o arquivo temporário.

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


        # ----------------------------------------------------
        # TEXTO PARA O TRELLO
        # ----------------------------------------------------

        print(
            "Gerando texto para o Trello..."
        )

        texto_trello = gerar_texto_trello(
            dados
        )


        caminho_trello = (
            PASTA_SAIDA /
            "texto_trello.txt"
        )


        caminho_trello.write_text(
            texto_trello,
            encoding="utf-8"
        )


        print(
            "Texto para o Trello "
            "gerado com sucesso!"
        )


        # ----------------------------------------------------
        # RESULTADO
        # ----------------------------------------------------

        return render_template(
            "resultado.html",
            dados=dados,
            nome_arquivo=nome_arquivo,
            texto_bloco=texto_bloco,
            texto_trello=texto_trello,
        )


    except Exception as erro:

        print()
        print(
            "ERRO DURANTE A ANÁLISE:"
        )

        print(
            repr(erro)
        )

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
        mimetype="text/plain; charset=utf-8",
    )


# ============================================================
# DOWNLOAD DO TEXTO PARA O TRELLO
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
        mimetype="text/plain; charset=utf-8",
    )


# ============================================================
# EXECUTAR LOCALMENTE
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=DEBUG
    )