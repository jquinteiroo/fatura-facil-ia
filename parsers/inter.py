from parsers.common import parse_standard

EXTRA_IGNORED = ("PAGAMENTO EFETUADO", "ESTORNO DE PAGAMENTO", "RESUMO DA FATURA")


def parse(text: str) -> list[dict]:
    return parse_standard(text, "inter", extra_ignored_terms=EXTRA_IGNORED)
