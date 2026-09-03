from app.monitoring.health import (
    _data_quality_score,
    _drift_score,
    _errors_score,
    _latency_score,
    _performance_score,
)


def test_performance_score_no_degradation():
    assert _performance_score(None) == 100
    assert _performance_score(0) == 100


def test_performance_score_degrades_with_degradation_pct():
    assert _performance_score(10) < 100
    assert _performance_score(30) < _performance_score(10)


def test_data_quality_score_mapping():
    class D:
        validation_status = "HEALTHY"

    class W:
        validation_status = "WARNING"

    class F:
        validation_status = "FAILED"

    assert _data_quality_score(D()) == 100
    assert _data_quality_score(W()) == 75
    assert _data_quality_score(F()) == 30
    assert _data_quality_score(None) == 100


def test_drift_score_mapping():
    assert _drift_score("NORMAL") == 96
    assert _drift_score("WARNING") == 70
    assert _drift_score("CRITICAL") == 35


def test_latency_score_within_budget():
    assert _latency_score(50) == 100
    assert _latency_score(0) == 100


def test_latency_score_over_budget():
    assert _latency_score(400) < 100


def test_errors_score_scales_with_rate():
    assert _errors_score(0.0) == 100
    assert _errors_score(0.1) < 100
    assert _errors_score(0.5) < _errors_score(0.1)
