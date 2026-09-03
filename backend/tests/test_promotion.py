from types import SimpleNamespace

from app.registry.registry_service import evaluate_promotion


def _model(f1, latency=50.0):
    return SimpleNamespace(metrics={"f1": f1, "inference_latency": latency})


def test_first_model_always_promoted():
    decision = evaluate_promotion(None, _model(0.5))
    assert decision["approved"] is True


def test_challenger_beats_champion_by_required_margin():
    champion = _model(0.80)
    challenger = _model(0.85)  # +0.05 > default min_improvement 0.02
    decision = evaluate_promotion(champion, challenger)
    assert decision["approved"] is True


def test_challenger_fails_insufficient_improvement():
    champion = _model(0.80)
    challenger = _model(0.805)  # +0.005 < 0.02
    decision = evaluate_promotion(champion, challenger)
    assert decision["approved"] is False


def test_challenger_rejected_on_latency_regression():
    champion = _model(0.80, latency=50.0)
    challenger = _model(0.90, latency=200.0)  # huge latency regression
    decision = evaluate_promotion(champion, challenger)
    assert decision["approved"] is False
    assert "latency" in decision["reason"]


def test_worse_challenger_rejected():
    champion = _model(0.90)
    challenger = _model(0.70)
    decision = evaluate_promotion(champion, challenger)
    assert decision["approved"] is False
