from parsers.common import parse_standard

EXTRA_IGNORED = ("DINHEIRO RECEBIDO", "VALOR DA FATURA", "RESUMO DE CONSUMO")


def parse(text: str) -> list[dict]:
    return parse_standard(
        text,
        "mercado_pago",
        extra_ignored_terms=EXTRA_IGNORED,
        replacements=(("Mercado Pago *", ""), ("MERCADO PAGO *", "")),
    )
