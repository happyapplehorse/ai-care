from unittest.mock import Mock

from ai_care.choice_execute import choice_execute


def test_choice_execute_choice_error():
    # Setup
    mock_ai_care = Mock()

    # Action
    choice_execute(ai_care=mock_ai_care, choice_code="EE", content="", depth_left=1)

    # Assert
    _, called_kwargs = mock_ai_care.ask.call_args
    assert "Your choice code EE is not correct." in called_kwargs["messages_list"][1]["content"]

def test_choice_execute_parse_json_error():
    # Setup
    mock_ai_care = Mock()
    mock_ai_care.ability.abilities = {
        "stay_silent": Mock(),
        "speak_now": Mock(),
        "speak_after": Mock()
    }

    # Action
    choice_execute(ai_care=mock_ai_care, choice_code="03", content="{wrong json string", depth_left=1)

    # Assert
    _, called_kwargs = mock_ai_care.ask.call_args
    assert "Failed to correctly parse the parameter." in called_kwargs["messages_list"][0]["content"]

def test_choice_execute_param_not_dict_error():
    # Setup
    mock_ai_care = Mock()
    mock_ai_care.ability.abilities = {
        "stay_silent": Mock(),
        "speak_now": Mock(),
        "speak_after": Mock()
    }

    # Action
    choice_execute(ai_care=mock_ai_care, choice_code="03", content='[{"role": "ai_care"}]', depth_left=1)

    # Assert
    _, called_kwargs = mock_ai_care.ask.call_args
    assert "The parameters should be a dictionary in JSON format." in called_kwargs["messages_list"][0]["content"]

def test_choice_execute_error():
    # Setup
    mock_ai_care = Mock()

    # Action
    choice_execute(ai_care=mock_ai_care, choice_code="00", content="", depth_left=1)

    # Assert
    mock_ai_care.ask.assert_called_with(messages_list=[], depth_left=0)

def test_choice_execute_stay_silent():
    # Setup
    mock_ai_care = Mock()
    mock_stay_silent_method = Mock()
    mock_speak_now_method = Mock()
    mock_speak_after_method = Mock()
    mock_ai_care.ability.abilities = {
        "stay_silent": mock_stay_silent_method,
        "speak_now": mock_speak_now_method,
        "speak_after": mock_speak_after_method
    }
    depth_left = 3
    choice_code = "01"
    content = "content"

    # Action
    choice_execute(ai_care=mock_ai_care, choice_code=choice_code, content=content, depth_left=depth_left)

    # Assert
    assert mock_stay_silent_method.called
    assert not mock_speak_now_method.called
    assert not mock_speak_after_method.called

def test_choice_execute_speak_now():
    # Setup
    mock_ai_care = Mock()
    mock_stay_silent_method = Mock()
    mock_speak_now_method = Mock()
    mock_speak_after_method = Mock()
    mock_ai_care.ability.abilities = {
        "stay_silent": mock_stay_silent_method,
        "speak_now": mock_speak_now_method,
        "speak_after": mock_speak_after_method
    }
    mock_speak_now_method._ability_parameters_ = [
        {
            "name": "content",
            "description": "The content you want to say",
            "param_type": "string",
            "required": True,
            "default_value": "",
        },
    ]
    mock_speak_now_method._auto_depth_ = False
    depth_left = 3
    choice_code = "02"
    content = "content"

    # Action
    choice_execute(ai_care=mock_ai_care, choice_code=choice_code, content=content, depth_left=depth_left)

    # Assert
    assert not mock_stay_silent_method.called
    assert not mock_speak_after_method.called
    assert mock_speak_now_method.called
    mock_speak_now_method.assert_called_with(content="content")

def test_choice_execute_speak_after():
    # Setup
    mock_ai_care = Mock()
    mock_stay_silent_method = Mock()
    mock_speak_now_method = Mock()
    mock_speak_after_method = Mock()
    mock_ai_care.ability.abilities = {
        "stay_silent": mock_stay_silent_method,
        "speak_now": mock_speak_now_method,
        "speak_after": mock_speak_after_method
    }
    mock_speak_after_method._ability_parameters_ = [
        {
            "name": "delay",
            "description": "",
            "param_type": "string",
            "required": True,
            "default_value": "",
        },
        {
            "name": "message",
            "description": "",
            "param_type": "string",
            "required": True,
            "default_value": "",
        },
    ]
    mock_speak_after_method._auto_depth_ = False
    depth_left = 3
    choice_code = "03"
    content = '{"delay": 1, "message": "message content"}'

    # Action
    choice_execute(ai_care=mock_ai_care, choice_code=choice_code, content=content, depth_left=depth_left)

    # Assert
    assert not mock_stay_silent_method.called
    assert not mock_speak_now_method.called
    assert mock_speak_after_method.called
    mock_speak_after_method.assert_called_with(delay=1, message="message content")
