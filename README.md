# AI-Care
![GitHub License](https://img.shields.io/github/license/happyapplehorse/ai-care)
![PyPI - Version](https://img.shields.io/pypi/v/ai-care)
![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/happyapplehorse/ai-care/python-publish.yml?logo=pypi)
![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/happyapplehorse/ai-care/codecov.yml?logo=pytest&label=test)
[![codecov](https://codecov.io/gh/happyapplehorse/ai-care/graph/badge.svg?token=G091OOWBDF)](https://codecov.io/gh/happyapplehorse/ai-care)
![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen)

Current AI models are only capable of passively responding to user inquiries
and lack the ability to initiate conversations.
AI-Care endows AI with the capability to speak proactively.
With simple settings, AI-Care allows your AI to proactively care for you.

## Highlights✨

1. 💵Low Cost: In terms of both token usage and API call frequencies, AI-Care is designed to minimize these expenses.
It operates with an O(1) cost complexity, which means that the costs do not increase with the duration of its activation.
2. 🕊️Low Intrusiveness: AI-Care provides its services alongside existing systems,
with virtually zero intrusion into the original code.
This allows for easy integration of AI-Care services into existing systems.
3. 🌍Model Universality: Compatible with all LLM (Large Language Model) models,
AI-Care does not rely on function call features or specific ways in which the model is used.

## Usage

1. Define the "to_llm" and "to_user" interfaces. AICare uses the "to_llm" interface to send
messages to the LLM and uses the "to_user" interface to send messages to the user.
```python
def to_llm_method(chat_context, to_llm_messages: list[AICareContext]) -> str | Generator[str, None, None]:
    # Here you need to convert `to_llm_messages` into the message format of the LLM you are using
    # and send the message to the LLM.
    # The return value is the message content replied by the LLM.
    # If you are not using stream mode, directly return the reply message string.
    # You can also use stream mode, in which case a string generator should be returned.
    # If using stream mode, AICare will also automatically use stream mode when sending messages to the user.
    pass

def to_user_method(to_user_message: str | Generator[str, None, None]) -> None:
    # Here you need to process messages from AICare as you would a normal LLM reply.
    # If using stream mode, this method should be able to receive and handle a string generator.
    # If the `to_llm` method uses stream mode, then this method should also use stream mode.
    pass
```

2. Instantiate AICare:
```python
ai_care = AICare()
```

3. Register "to_llm" and "to_user" methods:
```python
ai_care.register_to_llm_method(to_llm_method)
ai_care.register_to_user_method(to_user_method)
```

4. Using AICare
```python
# After each round of conversation or when AICare service is needed
ai_care.chat_update(chat_context)
```

## AI-Care settings
```python
# Set how long before AI-Care is activated
ai_care.set_config(key="delay", value=60)

# Set the number of times AI-Care selects “ASK_LATER”, setting it to 0 can disable this option.
ai_care.set_config(key="ask_later_count_limit", value=1)

# Set the system default recursive depth for ask.
ai_care.set_config(key="ask_depth", value=1)

# Set the maximum number of chat intervals the system automatically records.
ai_care.set_config(key="n_chat_intervals", value=20)
```

## License

This project is licensed under the [MIT License](./LICENSE).
