from orchestrator.intent import IntentPrediction, classify_intent


def test_classify_kpi_intent():
    prediction = classify_intent("Quel est le rendement actuel ?")
    assert prediction.label == "kpi"
    assert prediction.kpi_name == "rendement"


def test_classify_document_intent():
    prediction = classify_intent("Montre moi la procedure de sechage")
    assert prediction.label == "documents"


def test_classify_mixed_default():
    prediction = classify_intent("Peux tu aider ?")
    assert prediction.label == "mixed"
    assert prediction.kpi_name is None
