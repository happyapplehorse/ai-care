import time
from unittest.mock import Mock

from ai_care import AICare
from ai_care.abilities import Ability, _ability


def test_auto_register_abilities():
    class FakeAbility(Ability):
        @_ability(
            description="Fake_ability_description"
        )
        def fake_ability(self) -> str:
            return "Fake ability"

        def not_ability(self) -> str:
            return "Not ability"

    fake_ability = FakeAbility(Mock())

    abilities_list = list(fake_ability.abilities.keys())
    
    assert "fake_ability" in abilities_list
    assert "not_ability" not in abilities_list

    result = []
    for name, ability in fake_ability.abilities.items():
        if name == "fake_ability":
            assert ability._ability_description_ == "Fake_ability_description"
            result.append(ability())

    assert result == ["Fake ability"]

def test_abilities():
    # Setup
    response = (x for x in ['AA0', '0030', '3:{"delay":1,', '"message":', '"hi"}'])
    ai_care = AICare()
    ai_care.set_config(key="delay", value=0.1)
    to_user_method = Mock()
    to_llm_method = Mock()
    to_llm_method.return_value = response
    ai_care.register_to_llm_method(to_llm_method)
    ai_care.register_to_user_method(to_user_method)
    
    # Actions
    ai_care.chat_update(chat_context=[])
    
    # Assert
    time.sleep(0.2)
    assert to_llm_method.called
    time.sleep(1)
    assert to_user_method.called
    called_args, _ = to_user_method.call_args
    assert ''.join(x for x in called_args[0]) == "hi"
