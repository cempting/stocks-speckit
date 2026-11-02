from pathlib import Path

from market_leadership.config import load_settings


def test_company_evidence_settings_are_additive_and_have_safe_defaults(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("COMPANY_EVIDENCE_ROOT", raising=False)
    monkeypatch.delenv("SEC_EDGAR_USER_AGENT", raising=False)
    monkeypatch.delenv("MARKET_CATALOG_MANIFEST_PATH", raising=False)

    settings = load_settings()

    assert settings.company_evidence_root == ".data/company-evidence"
    assert settings.sec_edgar_user_agent == ""
    assert settings.default_provider == "yfinance"
    assert settings.provider_ids == ("yfinance",)


def test_company_evidence_root_and_sec_contact_are_configurable_but_private(
    monkeypatch, tmp_path: Path
) -> None:
    evidence_root = tmp_path / "private evidence"
    contact = "Research Team research@example.test"
    monkeypatch.setenv("COMPANY_EVIDENCE_ROOT", str(evidence_root))
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", contact)

    settings = load_settings()

    assert settings.company_evidence_root == str(evidence_root)
    assert settings.sec_edgar_user_agent == contact
    assert contact not in repr(settings)
