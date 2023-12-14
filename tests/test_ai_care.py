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
    ai_care.set_timer(interval=1, function=callback, args=callback_args, kwargs=callback_kwargs)

    # Assert
    time.sleep(0.9)
    assert not callback.called
    time.sleep(0.2)
    assert callback.called
    assert callback.call_count == 1
    callback.assert_called_with(*callback_args, **callback_kwargs)

