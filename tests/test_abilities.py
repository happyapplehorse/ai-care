from unittest.mock import Mock

from ai_care.abilities import Ability, _ability_description


def test_register_abilities():
    class FakeAbility(Ability):
        @_ability_description(
            description="Fake_ability_description"
        )
        def fake_ability(self) -> str:
            return "Fake ability"

        def not_ability(self) -> str:
            return "Not ability"

    fake_ability = FakeAbility(Mock())

    abilities_list = [ability.__name__ for ability in fake_ability.abilities]
    
    assert "fake_ability" in abilities_list
    assert "not_ability" not in abilities_list

    result = []
    for ability in fake_ability.abilities:
        if ability.__name__ == "fake_ability":
            assert ability._ability_description_ == "Fake_ability_description"
            result.append(ability())

    assert result == ["Fake ability"]
