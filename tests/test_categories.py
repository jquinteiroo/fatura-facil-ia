from core.categories import categorize


def test_common_categories():
    assert categorize("IFOOD *RESTAURANTE") == "Alimentação"
    assert categorize("UBER *TRIP") == "Transporte"
    assert categorize("NETFLIX.COM") == "Assinaturas"
    assert categorize("SUPERMERCADO ABC") == "Mercado"


def test_unknown_is_other():
    assert categorize("LOJA DESCONHECIDA XYZ") == "Outros"
