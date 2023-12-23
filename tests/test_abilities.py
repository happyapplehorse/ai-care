import pytest
import time
from unittest.mock import Mock

from ai_care import AICare
from ai_care.abilities import Ability, _ability


@pytest.fixture
def ai_care():
    ai_care = AICare()
    yield ai_care
    ai_care.clear_timer(clear_preserved=True, default_task_num_authority_external="Highest")

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

def test_abilities(ai_care: AICare):
    # Setup
    response = (x for x in ['AA0', '0030', '3:{"delay": 0.2, ', '"message": ', '"hi"}'])
    ai_care.set_config(key="delay", value=0.1)
    to_user_method = Mock()
    to_llm_method = Mock()
    to_llm_method.return_value = response
    ai_care.register_to_llm_method(to_llm_method)
    ai_care.register_to_user_method(to_user_method)
    
    # Action
    ai_care.chat_update(chat_context=[])
    
    # Assert
    time.sleep(0.2)
    assert to_llm_method.called
    time.sleep(0.2)
    assert to_user_method.called
    called_args, _ = to_user_method.call_args
    assert ''.join(x for x in called_args[0]) == "hi"

def test_detect_env(ai_care: AICare):
    # Setup
    ai_care.ask = Mock()
    mock_sensor = Mock()
    mock_sensor.return_value = "mock_sensor value"
    ai_care.sensors = {"mock_sensor": {"name": "mock_sensor", "function": mock_sensor, "annotation": "mock_sensor_annotation"}}

    # Action
    ai_care.ability.abilities["detect_env"](delay=0.1, sensors=["mock_sensor"], _depth_left=1)
    time.sleep(0.2)

    # Assert
    assert ai_care.ask.called
    _, called_kwargs = ai_care.ask.call_args
    assert "The results of the sensor are as follows: {'mock_sensor': 'mock_sensor value'}" in called_kwargs["messages_list"][0]["content"]

    # Action
    ai_care.ability.abilities["detect_env"](delay=0.1, sensors=["mock_sensor_not_existed"], _depth_left=1)
    time.sleep(0.2)

    # Assert
    _, called_kwargs = ai_care.ask.call_args
    assert "There are no {'mock_sensor_not_existed'} sensor." in called_kwargs["messages_list"][0]["content"]

def test_release_detector(ai_care: AICare):
    # Setup
    ai_care.ask = Mock()
    mock_detector = Mock()
    ai_care.detectors = {"mock_detector": mock_detector}
    mock_release_detector = Mock()
    ai_care.release_detector = mock_release_detector

    # Action
    ai_care.ability.abilities["release_detector"](delay=0.1, detectors=["mock_detector_not_existed"], _depth_left=1)

    # Assert
    assert ai_care.ask.called
    _, called_kwargs = ai_care.ask.call_args
    assert "There are no {'mock_detector_not_existed'} detector." in called_kwargs["messages_list"][0]["content"]
    
    # Action
    ai_care.ability.abilities["release_detector"](delay=0.1, detectors=["mock_detector"], _depth_left=1)
    time.sleep(0.2)

    # Assert
    mock_release_detector.assert_called_with(["mock_detector"])

def test_ask_later(ai_care: AICare):
    # Setup
    ai_care.ask = Mock()

    # Action
    ai_care._ask_later_count_left = 0
    ai_care.ability.abilities["ask_later"](delay=0.1, _depth_left=1)
    time.sleep(0.2)

    # Assert
    assert not ai_care.ask.called
    
    # Action
    ai_care._ask_later_count_left = 1
    ai_care.ability.abilities["ask_later"](delay=0.1, _depth_left=1)
    time.sleep(0.2)

    # Assert
    _, called_kwargs = ai_care.ask.call_args
    assert "0.1 seconds have passed. Please make a choice." in called_kwargs["messages_list"][0]["content"]
    
    # Action
    ai_care.ability.abilities["ask_later"](delay=0.1, _depth_left=1)
    time.sleep(0.2)

    # Assert
    assert ai_care.ask.call_count == 1

def test_cyclic_detection(ai_care: AICare):
    # Setup
    ai_care.ask = Mock()
    mock_detector = Mock()
    ai_care.detectors = {"mock_detector": mock_detector}
    mock_release_detector = Mock()
    ai_care.release_detector = mock_release_detector

    # Action
    ai_care.ability.abilities["cyclic_detection"](interval=0.1, detectors=["mock_detector_not_existed"], _depth_left=1)
    time.sleep(0.2)

    # Assert
    _, called_kwargs = ai_care.ask.call_args
    assert "There are no {'mock_detector_not_existed'} detector." in called_kwargs["messages_list"][0]["content"]
    assert not mock_release_detector.called
    
    # Action
    ai_care.ability.abilities["cyclic_detection"](interval=0.1, detectors=["mock_detector"], _depth_left=1)
    time.sleep(0.35)
    ai_care.clear_timer()
    time.sleep(0.3)

    # Assert
    assert mock_release_detector.call_count == 3
