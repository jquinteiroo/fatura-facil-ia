from parsers.common import parse_standard

EXTRA_IGNORED = (
    "CRÉDITO RECEBIDO", "CREDITO RECEBIDO", "AJUSTE A CRÉDITO", "AJUSTE A CREDITO",
)


def parse(text: str) -> list[dict]:
    return parse_standard(text, "nubank", extra_ignored_terms=EXTRA_IGNORED)
