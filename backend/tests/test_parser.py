from app.services.parser import SignalParser


def test_rules_parser_extracts_common_signal():
    result = SignalParser().parse("BUY EURUSD ENTRY 1.0720 SL 1.0680 TP1 1.0780 RISK 1%")
    assert result.is_valid
    assert result.symbol == "EURUSD"
    assert result.side == "buy"
    assert result.stop_loss == 1.0680
