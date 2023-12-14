from unittest.mock import Mock

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
