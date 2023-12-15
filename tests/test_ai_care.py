import time
from unittest.mock import Mock

from ai_care import AICare


def test_set_timer():
    # Setup
    ai_care = AICare()
    
    callback = Mock()
    callback_args = ("arg1", "arg2")
    callback_kwargs = {"kwarg1": "value1", "kwarg2": "value2"}

    # Actions
    timer_id = ai_care.set_timer(interval=1, function=callback, args=callback_args, kwargs=callback_kwargs)

    # Assert
    assert timer_id in ai_care.timers
    time.sleep(0.9)
    assert not callback.called
    time.sleep(0.2)
    assert callback.called
    assert callback.call_count == 1
    callback.assert_called_with(*callback_args, **callback_kwargs)
    assert timer_id not in ai_care.timers

def test_timer_cancel():
    # Setup
    ai_care = AICare()
    
    callback = Mock()
    callback_args = ("arg1", "arg2")
    callback_kwargs = {"kwarg1": "value1", "kwarg2": "value2"}

    # Actions
    timer_id = ai_care.set_timer(interval=1, function=callback, args=callback_args, kwargs=callback_kwargs)

    # Assert
    assert timer_id in ai_care.timers

    # Actions
    time.sleep(0.5)
    ai_care.timer_cancel(timer_id)

    # Assert
    assert timer_id not in ai_care.timers
    time.sleep(0.6)
    assert not callback.called

def test_set_guide():
    # Setup
    ai_care = AICare()

    # Actions
    ai_care.set_guide("You are a considerate person who cars about others.")

    # Assert
    assert ai_care.guide == "You are a considerate person who cars about others."
