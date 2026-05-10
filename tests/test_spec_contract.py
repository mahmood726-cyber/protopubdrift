from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "superpowers" / "specs" / "2026-04-14-proto-pub-drift-design.md"


def test_proto_pub_drift_spec_declares_six_axes_and_sources():
    text = SPEC.read_text(encoding="utf-8")
    required = [
        "Primary outcome",
        "Sample size",
        "Eligibility",
        "Analysis plan",
        "Subgroup list",
        "Follow-up duration",
        "AACT",
        "PMC full-text XML",
    ]
    missing = [marker for marker in required if marker not in text]
    assert missing == []


def test_proto_pub_drift_spec_has_accuracy_and_truth_gates():
    text = SPEC.read_text(encoding="utf-8")
    required = [
        "accuracy below 0.80 blocks",
        "hand-audit",
        "fail-closed",
        "TruthCert",
        "data/drift_cards.csv",
        "Not parsing paywalled PDFs",
        "OA-only",
    ]
    missing = [marker for marker in required if marker not in text]
    assert missing == []
