import os
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


# ============================================================
# CONFIGURAÇÃO
# ============================================================

load_dotenv()

# DEBUG só fica ligado se FLASK_DEBUG=1 estiver definido no
# ambiente (.env). Em produção, não defina essa variável.
DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

app = Flask(
    __name__,
    template_folder="interface/templates",
    static_folder="interface/static",
)


PASTA_SAIDA = Path("saida")
PASTA_EDITAIS = Path("editais")

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
                erro="Nenhum arquivo PDF foi selecionado."
            )

        if not arquivo.filename:

            return render_template(
                "erro.html",
                erro="O arquivo selecionado não possui nome."
            )

        # ----------------------------------------------------
        # VALIDAR PDF
        # ----------------------------------------------------

        # secure_filename remove ../, barras e caracteres
        # perigosos do nome do arquivo enviado pelo usuário,
        # evitando que ele grave fora da pasta "editais".
        nome_arquivo = secure_filename(
            arquivo.filename
        )

        if not nome_arquivo:

            return render_template(
                "erro.html",
                erro="Nome de arquivo inválido."
            )

        if not nome_arquivo.lower().endswith(".pdf"):

            return render_template(
                "erro.html",
                erro="O arquivo precisa estar no formato PDF."
            )

        # ----------------------------------------------------
        # SALVAR PDF
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
        print("Lendo edital...")

        texto = extrair_texto_pdf(
            str(caminho_pdf)
        )

        if not texto.strip():

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
            "Enviando edital para análise da IA..."
        )

        dados = extrair_dados_com_ia(
            texto
        )

        # ----------------------------------------------------
        # FILTRO DELTA
        # ----------------------------------------------------

        print(
            "Procurando produtos compatíveis "
            "na tabela DELTA..."
        )

        dados = filtrar_itens(
            dados
        )

        # ----------------------------------------------------
        # MOSTRAR ITENS NO TERMINAL
        # ----------------------------------------------------

        print()
        print(
            "ITENS ENCONTRADOS NA TABELA DELTA:"
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

        gerar_bloco_notas(
            dados,
            str(caminho_bloco)
        )

        print(
            "Bloco de notas gerado com sucesso!"
        )

        print(
            f"Arquivo: {caminho_bloco}"
        )

        print()

        # ----------------------------------------------------
        # RESULTADO
        # ----------------------------------------------------

        return render_template(
            "resultado.html",
            dados=dados,
            nome_arquivo=nome_arquivo,
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

@app.route("/download")
def download():

    caminho_saida = (
        PASTA_SAIDA /
        "bloco_notas.txt"
    )

    if not caminho_saida.exists():

        return render_template(
            "erro.html",
            erro=(
                "O bloco de notas ainda "
                "não foi gerado."
            )
        ), 404

    return send_file(
        caminho_saida,
        as_attachment=True,
        download_name="bloco_notas.txt",
        mimetype="text/plain",
    )


# ============================================================
# EXECUTAR
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=DEBUG
    )