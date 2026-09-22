from parsers.common import parse_standard

EXTRA_IGNORED = ("CRÉDITO AUTOMÁTICO", "CREDITO AUTOMATICO", "DEMONSTRATIVO DA FATURA")


def parse(text: str) -> list[dict]:
    return parse_standard(text, "sicredi", extra_ignored_terms=EXTRA_IGNORED)
