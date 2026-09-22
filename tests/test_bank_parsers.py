from core.parser import parse_transactions


def test_nubank_layout():
    result = parse_transactions("""
    Nubank
    03 SET IFOOD *RESTAURANTE R$ 45,90
    04 SET UBER *TRIP R$ 21,10
    """)
    assert result["analysis"]["parser"] == "nubank"
    assert result["total"] == 67.00


def test_inter_multiline_layout():
    result = parse_transactions("""
    Banco Inter
    03/09
    SUPERMERCADO ABC
    126,40
    04/09 NETFLIX.COM 39,90
    """)
    assert result["analysis"]["parser"] == "inter"
    assert len(result["transactions"]) == 2
    assert result["total"] == 166.30


def test_mercado_pago_layout():
    result = parse_transactions("""
    Mercado Pago
    03-09 MERCADO PAGO *IFOOD 52,50
    04-09 UBER TRIP 18,20
    """)
    assert result["analysis"]["parser"] == "mercado_pago"
    assert result["transactions"][0]["Categoria"] == "Alimentação"


def test_sicredi_installment_layout():
    result = parse_transactions("""
    Sicredi
    05/09 LOJA EXEMPLO PARC 2/6 199,90
    """)
    tx = result["transactions"][0]
    assert result["analysis"]["parser"] == "sicredi"
    assert tx["ParcelaAtual"] == 2
    assert tx["ParcelasTotal"] == 6
