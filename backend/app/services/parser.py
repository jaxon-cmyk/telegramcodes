import re
from dataclasses import dataclass, field


SYMBOL_RE = re.compile(r"\b([A-Z]{6}|XAUUSD|XAGUSD|US30|NAS100|SPX500)\b")
SIDE_RE = re.compile(r"\b(BUY|SELL|LONG|SHORT)\b", re.IGNORECASE)
NUMBER_RE = r"([0-9]+(?:\.[0-9]+)?)"
IGNORED_SYMBOL_WORDS = {"ENTRY", "ENTER", "SIGNAL", "UPDATE", "MARKET"}


@dataclass
class ParseResult:
    symbol: str | None = None
    side: str | None = None
    entry: float | None = None
    stop_loss: float | None = None
    take_profits: list[float] = field(default_factory=list)
    lot: float | None = None
    risk_percent: float | None = None
    confidence: float = 0
    parser_source: str = "rules"
    explanation: str = ""
    rejection_reason: str | None = None

    @property
    def is_valid(self) -> bool:
        return bool(self.symbol and self.side and self.stop_loss and (self.entry or self.take_profits))


class SignalParser:
    def parse(self, text: str) -> ParseResult:
        result = self._parse_with_rules(text)
        if result.is_valid:
            return result
        return self._ai_assisted_fallback(text, result)

    def _parse_with_rules(self, text: str) -> ParseResult:
        upper = text.upper()
        side_match = SIDE_RE.search(upper)
        symbol_match = next((match for match in SYMBOL_RE.finditer(upper) if match.group(1) not in IGNORED_SYMBOL_WORDS), None)
        entry_match = re.search(rf"(?:ENTRY|ENTER|@)\s*[:@-]?\s*{NUMBER_RE}", upper)
        sl_match = re.search(rf"(?:SL|STOP\s*LOSS)\s*[:@-]?\s*{NUMBER_RE}", upper)
        tp_matches = re.findall(rf"(?:TP\d*|TAKE\s*PROFIT)\s*[:@-]?\s*{NUMBER_RE}", upper)
        lot_match = re.search(rf"(?:LOT|LOTS|VOLUME)\s*[:@-]?\s*{NUMBER_RE}", upper)
        risk_match = re.search(rf"(?:RISK)\s*[:@-]?\s*{NUMBER_RE}\s*%?", upper)

        side = side_match.group(1).lower() if side_match else None
        if side == "long":
            side = "buy"
        if side == "short":
            side = "sell"

        result = ParseResult(
            symbol=symbol_match.group(1) if symbol_match else None,
            side=side,
            entry=float(entry_match.group(1)) if entry_match else None,
            stop_loss=float(sl_match.group(1)) if sl_match else None,
            take_profits=[float(value) for value in tp_matches],
            lot=float(lot_match.group(1)) if lot_match else None,
            risk_percent=float(risk_match.group(1)) if risk_match else None,
            confidence=0.86 if side_match and symbol_match and sl_match else 0.45,
            explanation="Rules parser extracted symbol, side, entry, SL/TP, lot, and risk fields from common signal labels.",
        )
        if not result.is_valid:
            missing = []
            if not result.symbol:
                missing.append("symbol")
            if not result.side:
                missing.append("side")
            if not result.stop_loss:
                missing.append("stop loss")
            if not (result.entry or result.take_profits):
                missing.append("entry or take profit")
            result.rejection_reason = f"Missing required fields: {', '.join(missing)}"
        return result

    def _ai_assisted_fallback(self, text: str, prior: ParseResult) -> ParseResult:
        # Provider hook: an OpenAI or other parser can be wired here. Keep v1 safe by
        # returning a review result unless structured output passes normal validation.
        prior.parser_source = "ai_fallback_stub"
        prior.confidence = min(prior.confidence, 0.35)
        prior.explanation += " AI fallback is configured as a validation hook; no unvalidated AI trade output was accepted."
        return prior
