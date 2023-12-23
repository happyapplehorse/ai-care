import pytest
import textwrap
from enum import Enum
from unittest.mock import Mock, patch

from ai_care import AICare
from ai_care.render_prompt import _render_ability_description, render_basic_prompt


@pytest.fixture
def ai_care():
    ai_care = AICare()
    yield ai_care
    ai_care.clear_timer(clear_preserved=True, default_task_num_authority_external="Highest")

def test_render_ability_description():
    
    # Setup
    class MockChoice(Enum):
        STAY_SILENT = "01"
        SPEAK_NOW = "02"
        WITH_PARAMETER = "03"

    ability1, ability2, ability3 = Mock(), Mock(), Mock()
    
    ability1.__name__ = "stay_silent"
    ability1._ability_description_ = "ability stay silent have no parameter"
    ability1._ability_parameters_ = []
    
    ability2.__name__ = "speak_now"
    ability2._ability_description_ = "ability speak now is not a form of parameter calling; it derectly provides content"
    ability2._ability_parameters_ = []

    ability3.__name__ = "with_parameter"
    ability3._ability_description_ = "ability with parameter description"
    ability3._ability_parameters_ = [
        {
            "name": "param_1",
            "param_type": "list[str]",
            "description": "param_1 description",
            "required": True,
            "default_value": [],
        },
        {
            "name": "param_2",
            "param_type": "string",
            "description": "param_2 description",
            "required": False,
            "default_value": "default value",
        },
    ]
    
    # Action
    with patch('ai_care.render_prompt.Choice', MockChoice):
        prompt1 = _render_ability_description(ability1)
        prompt2 = _render_ability_description(ability2)
        prompt3 = _render_ability_description(ability3)
    
    # Assert
    assert prompt1 == textwrap.dedent(
        """
        Choice code: 01
        Choice description: ability stay silent have no parameter
        Choice content: Empty

        """
    )
    assert prompt2 == textwrap.dedent(
        """
        Choice code: 02
        Choice description: ability speak now is not a form of parameter calling; it derectly provides content
        Choice content: The content you want to say

        """
    )
    assert prompt3 == textwrap.dedent(
        """
        Choice code: 03
        Choice description: ability with parameter description
        Choice content: Provide the values of the following parameters in JSON format
            Parameter name: param_1
            Parameter description: param_1 description
            Parameter type: list[str]
            This parameter must be provided
            
            Parameter name: param_2
            Parameter description: param_2 description
            Parameter type: string
            This parameter is optional, with a default value: default value

        """
    )

def test_render_basic_prompt(ai_care: AICare):
    prompt = render_basic_prompt(ai_care)
    assert isinstance(prompt, str)
