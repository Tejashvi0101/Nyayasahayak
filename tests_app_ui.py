from streamlit.testing.v1 import AppTest

def test_streamlit_ui():
    print("Testing Streamlit UI in Project 2...")
    at = AppTest.from_file("app.py", default_timeout=25)
    at.run()
    assert not at.exception, f"App crashed on launch: {at.exception}"
    print(">> App loaded without errors.")

    # Check metrics
    print(f">> Total metrics displayed: {len(at.metric)}")
    for m in at.metric:
        print(f"   Metric: {m.label} = {m.value}")

    # Check tabs
    print(f">> Tabs present: {len(at.tabs)}")

    # Verify deterministic mode and API key inputs are NOT exposed in the UI
    router_sb = next(sb for sb in at.selectbox if "AI Router" in sb.label)
    assert all("deterministic" not in opt.lower() for opt in router_sb.options), "Deterministic mode should not be shown in UI"
    llm_model_sb = next(sb for sb in at.selectbox if "Select Model" in sb.label)
    assert "gemini-2.5-flash" in llm_model_sb.options and "gemini-2.5-pro" in llm_model_sb.options
    model_sb = next(sb for sb in at.selectbox if "Model Engine Profile" in sb.label)
    assert all("deterministic" not in opt.lower() for opt in model_sb.options), "Deterministic mode should not be shown in UI"
    assert not any("api key" in ti.label.lower() for ti in at.text_input), "API Key input should not be shown in UI"

    # Now simulate user selecting '✍️ Write My Own Problem'
    # Preset selectbox is at index 0 of selectboxes
    sb = at.sidebar.selectbox[0]
    sb.select("✍️ Write My Own Problem")
    at.run()
    assert not at.exception, f"App crashed after choosing 'Write My Own Problem': {at.exception}"
    print(">> Selected '✍️ Write My Own Problem' successfully.")

    # Verify that info message appears when text area is empty
    assert len(at.info) > 0
    print(">> Info prompt shown when story is empty.")

    # Now simulate user typing their custom problem
    custom_text = "I ordered an air conditioner for Rs 34000 on Flipkart, delivered defective, company refused return."
    ta = at.text_area[0]
    ta.input(custom_text)
    at.run()
    assert not at.exception, f"App crashed after typing custom problem: {at.exception}"
    print(f">> Custom story processed! Metrics: {[m.value for m in at.metric]}")
    assert any("Consumer" in str(m.value) for m in at.metric)
    assert any("34,000" in str(m.value) for m in at.metric)
    print(">> Domain and Amount correctly extracted for custom input in UI!")

    print("ALL STREAMLIT APP TESTS PASSED!")

if __name__ == "__main__":
    test_streamlit_ui()
