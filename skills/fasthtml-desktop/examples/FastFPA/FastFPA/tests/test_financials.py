from __future__ import annotations

import pytest

import db


@pytest.fixture()
def seeded(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "fastfpa-test.sqlite")
    db.seed()
    return db


def test_every_scenario_balances_and_cash_reconciles(seeded):
    for scenario in ("actual", "budget", "baseline", "upside", "downside"):
        periods = seeded.financial_periods(scenario)
        assert periods
        for row in periods:
            assets = row["cash"] + row["ar"] + row["inventory"] + row["fixed_assets"]
            liabilities_equity = row["ap"] + row["debt"] + row["equity"]
            assert assets == pytest.approx(liabilities_equity, abs=0.02)
            assert row["balance_check"] == pytest.approx(0, abs=0.02)
            assert row["cash_check"] == pytest.approx(0, abs=0.02)


def test_scenario_change_recalculates_without_mutating_budget(seeded):
    before = seeded.annual_summary("baseline")["revenue"]
    budget_before = seeded.annual_summary("budget")["revenue"]
    seeded.update_assumptions("baseline", {"monthly_growth": "2.5"}, "test@example.com")
    after = seeded.annual_summary("baseline")["revenue"]
    assert after > before
    assert seeded.annual_summary("budget")["revenue"] == budget_before


def test_actual_is_locked(seeded):
    with pytest.raises(ValueError):
        seeded.update_assumptions("actual", {"monthly_growth": "5"}, "test@example.com")


def test_recurring_customer_roll_forward(seeded):
    data = seeded.recurring("baseline")
    for previous, current in zip(data, data[1:]):
        assert previous["ending_customers"] == current["opening_customers"]
        assert current["ending_customers"] == (
            current["opening_customers"]
            + current["new_customers"]
            - current["churned_customers"]
        )
