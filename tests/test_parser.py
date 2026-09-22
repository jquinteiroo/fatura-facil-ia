from core.parser import detect_bank, parse_amount, parse_transactions


def test_amount_formats():
    assert parse_amount("1.234,56") == 1234.56
    assert parse_amount("48,90") == 48.90
    assert parse_amount("48.90") == 48.90


def test_detect_bank():
    assert detect_bank("Nubank - sua fatura") == "nubank"
    assert detect_bank("BANCO INTER") == "inter"


def test_parse_transactions_and_ignore_payment():
    text = """
    Nubank
    12 SET IFOOD *RESTAURANTE 48,90
    13 SET UBER *TRIP 21,50
    14 SET PAGAMENTO DE FATURA 500,00
    15/09 NETFLIX.COM 39,90
    """
    result = parse_transactions(text)
    assert result["bank"] == "nubank"
    assert len(result["transactions"]) == 3
    assert result["total"] == 110.30
    assert result["transactions"][0]["Categoria"] == "Alimentação"
