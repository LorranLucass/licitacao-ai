from pathlib import Path
import pymupdf


def extrair_texto_pdf(caminho_pdf: str) -> str:
    caminho = Path(caminho_pdf)

    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho}"
        )

    if caminho.suffix.lower() != ".pdf":
        raise ValueError("O arquivo precisa ser um PDF.")

    texto_paginas = []

    documento = pymupdf.open(str(caminho))

    try:
        for numero_pagina, pagina in enumerate(documento, start=1):
            texto = pagina.get_text("text").strip()

            if texto:
                texto_paginas.append(
                    f"\n{'=' * 60}\n"
                    f"PÁGINA {numero_pagina}\n"
                    f"{'=' * 60}\n\n"
                    f"{texto}"
                )

    finally:
        documento.close()

    return "\n".join(texto_paginas)