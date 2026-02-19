from src.nlp.processor import NLPProcessor

def test_pii_masking():
    processor = NLPProcessor()
    
    text = "Contact me at user@example.com or 123-456-7890. IP is 192.168.1.1."
    masked = processor.mask_pii(text)
    
    print(f"Original: {text}")
    print(f"Masked:   {masked}")
    
    assert "<EMAIL>" in masked
    assert "<PHONE>" in masked
    assert "<IP>" in masked
    assert "user@example.com" not in masked
    assert "123-456-7890" not in masked
    assert "192.168.1.1" not in masked
    print("PII Masking Test Passed!")

def test_llm_success():
    processor = NLPProcessor()
    result = processor.process_issue("System crash", "Server crashed due to memory leak.")
    
    print("\nLLM Result:")
    print(result.model_dump_json(indent=2))
    
    if result.root_cause_hypothesis != "Analysis failed":
        print("LLM Analysis Test Passed! (Real response received)")
    else:
        print("LLM Analysis Failed (Still getting fallback result)")

if __name__ == "__main__":
    test_pii_masking()
    test_llm_success()
