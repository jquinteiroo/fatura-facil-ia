from parsers import generic, inter, mercado_pago, nubank, sicredi
from parsers.common import parse_amount

BANK_MARKERS = {
    "nubank": ("NUBANK", "NU PAGAMENTOS"),
    "inter": ("BANCO INTER", "INTER PAGAMENTOS", "INTER&CO"),
    "mercado_pago": ("MERCADO PAGO", "MERCADOPAGO"),
    "sicredi": ("SICREDI",),
}

PARSERS = {
    "nubank": nubank.parse,
    "inter": inter.parse,
    "mercado_pago": mercado_pago.parse,
    "sicredi": sicredi.parse,
}


def detect_bank(text: str) -> str:
    upper = (text or "").upper()
    for bank, markers in BANK_MARKERS.items():
        if any(marker in upper for marker in markers):
            return bank
    return "desconhecido"


def build_analysis(transactions: list[dict], bank: str, parser_name: str) -> dict:
    positives = [item for item in transactions if float(item.get("Valor", 0) or 0) > 0]
    uncategorized = sum(1 for item in positives if (item.get("Categoria") or "Outros") == "Outros")
    categorized = len(positives) - uncategorized
    coverage = round((categorized / len(positives) * 100), 1) if positives else 0.0

    status = "ok"
    if bank == "desconhecido" or coverage < 60:
        status = "revisar"

    return {
        "bank": bank,
        "parser": parser_name,
        "transactions_count": len(positives),
        "categorized_count": categorized,
        "uncategorized_count": uncategorized,
        "category_coverage": coverage,
        "status": status,
    }


def parse_transactions(text: str) -> dict:
    bank = detect_bank(text)
    parser = PARSERS.get(bank)
    if parser:
        transactions = parser(text)
        parser_name = bank
    else:
        transactions = generic.parse(text, bank=bank)
        parser_name = "generico"

    total = round(sum(
        float(item.get("Valor", 0) or 0)
        for item in transactions
        if float(item.get("Valor", 0) or 0) > 0
    ), 2)

    return {
        "bank": bank,
        "transactions": transactions,
        "total": total,
        "analysis": build_analysis(transactions, bank, parser_name),
    }
