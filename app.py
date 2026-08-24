from services.pdf_reader import extrair_texto_pdf
from services.ai_extractor import extrair_dados_com_ia
from services.bloco_notas import gerar_bloco_notas
from services.item_matcher import (
    carregar_produtos,
    filtrar_itens
)


def main():

    print("================================")
    print("         LICITAÇÃO AI")
    print("================================")
    print()

    caminho_pdf = input(
        "Digite o caminho do edital PDF: "
    ).strip()

    try:

        print()
        print("Lendo edital...")

        texto = extrair_texto_pdf(caminho_pdf)

        print("Enviando edital para análise da IA...")

        dados = extrair_dados_com_ia(texto)

        # Filtra somente os produtos do Pelotão DELTA
        dados = filtrar_itens(dados)

        print()
        print("ITENS ENCONTRADOS NA TABELA DELTA:")
        print("----------------------------------")

        for item in dados.get("itens", []):

            print(
                f"Item {item.get('item')}: "
                f"{item.get('produto_tabela')}"
            )

            print(
                f"Marca: {item.get('marca_tabela')}"
            )

            print(
                f"Custo: {item.get('custo')}"
            )

            print(
                f"Mín. Feirão: "
                f"{item.get('minimo_feirao')}"
            )

        # Gera o bloco de notas
        gerar_bloco_notas(
            dados,
            "saida/bloco_notas.txt"
        )

        print(
            "Bloco de notas gerado com sucesso!"
        )

        print(
            "Arquivo: saida/bloco_notas.txt"
        )

        print()
        print("QUANTIDADE DE PRODUTOS NA TABELA DELTA:")

        produtos = carregar_produtos()

        print(len(produtos))

    except Exception as erro:

        print()
        print(f"Erro: {erro}")


if __name__ == "__main__":
    main()