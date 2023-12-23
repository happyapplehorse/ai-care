import pytest
import time
from unittest.mock import Mock, patch

from ai_care import AICare, Detector


@pytest.fixture
def ai_care():
    ai_care = AICare()
    yield ai_care
    ai_care.clear_timer(clear_preserved=True, default_task_num_authority_external="Highest")

def test_set_timer(ai_care: AICare):
    # Setup
    callback = Mock()
    callback_args = ("arg1", "arg2")
    callback_kwargs = {"kwarg1": "value1", "kwarg2": "value2"}

    # Action
    timer_id = ai_care.set_timer(interval=0.2, function=callback, args=callback_args, kwargs=callback_kwargs)

    # Assert
    assert timer_id in ai_care.timers
    time.sleep(0.1)
    assert not callback.called
    time.sleep(0.2)
    assert callback.called
    assert callback.call_count == 1
    callback.assert_called_with(*callback_args, **callback_kwargs)
    assert timer_id not in ai_care.timers

def test_timer_cancel(ai_care: AICare):
    # Setup
    callback = Mock()
    callback_args = ("arg1", "arg2")
    callback_kwargs = {"kwarg1": "value1", "kwarg2": "value2"}

    # Action
    timer_id = ai_care.set_timer(interval=0.2, function=callback, args=callback_args, kwargs=callback_kwargs)

    # Assert
    assert timer_id in ai_care.timers

    # Action
    time.sleep(0.1)
    ai_care.timer_cancel(timer_id)

    # Assert
    assert timer_id not in ai_care.timers
    time.sleep(0.2)
    assert not callback.called

def test_set_guide(ai_care: AICare):
    # Action
    ai_care.set_guide("You are a considerate person who cars about others.")

    # Assert
    assert ai_care.guide == "You are a considerate person who cars about others."

def test_task_num(ai_care: AICare):
    # Setup
    ai_care._task_num = 5
    
    flag = 0
    def callback(ai_care: AICare) -> None:
        nonlocal flag
        task_num = ai_care._get_task_num()
        flag = task_num
    
    # Action
    ai_care.set_timer(interval=0.1, function=callback, args=(ai_care,), task_num=3)
    time.sleep(0.2)

    # Assert
    assert ai_care._get_task_num() == 5
    assert flag == 3

    # Action
    ai_care.set_timer(interval=0.1, function=callback, args=(ai_care,))
    time.sleep(0.2)

    # Assert
    assert flag == 5

def test_clear_timer(ai_care: AICare):
    # Setup
    callback1 = Mock()
    callback2 = Mock()
    callback3 = Mock()
    callback4 = Mock()

    # Action
    ai_care._task_num = 1
    ai_care.set_timer(interval=0.1, function=callback1)
    ai_care._task_num = 2
    ai_care.set_timer(interval=0.1, function=callback2)
    ai_care.clear_timer(task_num_authority=1)
    time.sleep(0.2)

    # Assert
    assert not callback1.called
    assert callback2.called

    # Action
    def cancel_timer(ai_care: AICare):
        ai_care.clear_timer()
    ai_care._task_num = 1
    ai_care.set_timer(interval=0.2, function=callback3)
    ai_care.set_timer(interval=0.1, function=cancel_timer, kwargs={"ai_care": ai_care})
    ai_care._task_num = 2
    ai_care.set_timer(interval=0.2, function=callback4)
    time.sleep(0.3)

    # Assert
    assert not callback3.called
    assert callback4.called

def test_insert_chat_interval(ai_care: AICare):
    # Action
    for i in range(5):
        ai_care._insert_chat_interval(i)

    # Assert
    assert [int(i) for i in ai_care._chat_intervals] == [0, 1, 2, 3, 4]
    
    # Action
    for i in range(1, 31):
        ai_care._insert_chat_interval(i)

    # Assert
    assert [int(i) for i in ai_care._chat_intervals] == list(range(11, 31))

def test_chat_update(ai_care: AICare):
    # Setup
    mock_ask = Mock()
    
    # Action
    ai_care.set_config(key="delay", value=0.1)
    ai_care.set_config(key="ask_later_count_limit", value=1)
    ai_care.set_timer(interval=0.1, function=Mock())
    ai_care.ask = mock_ask
    ai_care.chat_update(chat_context=["chat_context"])
    time.sleep(0.2)

    # Assert
    assert ai_care._task_num == 2
    assert ai_care._chat_intervals == []
    assert ai_care.chat_context == ["chat_context"]
    assert ai_care._ask_later_count_left == 1
    assert ai_care.timers == {}
    assert mock_ask.called

def test_reset(ai_care: AICare):
    # Setup
    mock_task = Mock()
    ai_care._valid_msg_count = 10
    ai_care._invalid_msg_count = 10
    ai_care._last_chat_time = 10
    ai_care._chat_intervals = [10,10]
    ai_care.set_timer(interval=0.1, function=mock_task, preserve=True)

    # Action
    ai_care.reset()
    time.sleep(0.2)
    
    # Assert
    assert ai_care._valid_msg_count == 0
    assert ai_care._invalid_msg_count == 0
    assert ai_care._last_chat_time is None
    assert ai_care._chat_intervals == []
    assert not mock_task.called

def test_check_task_validity(ai_care: AICare):
    # Setup
    tasks_validity = []
    def check_validity(ai_care: AICare, validity_list: list):
        validity_list.append(ai_care._check_task_validity())

    # Action
    ai_care.set_timer(interval=0.1, function=check_validity, args=(ai_care, tasks_validity))
    ai_care.cancel_current_task()
    ai_care.set_timer(interval=0.1, function=check_validity, args=(ai_care, tasks_validity))
    time.sleep(0.2)

    # Assert
    assert tasks_validity == [False, True]

def test_ask(ai_care: AICare):
    # Setup
    mock_to_llm_method = Mock()
    mock_to_llm_method.return_value = "AA000101:"

    ai_care._to_llm_method = mock_to_llm_method

    # Action
    ai_care.ask(messages_list=[], depth_left=-1)

    # Assert
    assert not mock_to_llm_method.called

    # Action
    with patch('ai_care.ai_care.parse_response') as mock_pares_response, \
        patch('ai_care.ai_care.choice_execute') as mock_choice_execute:
        mock_pares_response.return_value = ("01", "")
        ai_care.ask(messages_list=[])

    # Assert
    assert mock_to_llm_method.called
    assert mock_pares_response.called
    assert mock_choice_execute.called
    mock_choice_execute.assert_called_with(
        ai_care=ai_care,
        choice_code="01",
        content="",
        depth_left=ai_care._config["ask_depth"]
    )

def test_trigger(ai_care: AICare):
    # Setup
    mock_ask = Mock()
    mock_release_detector = Mock()
    mock_detector = Mock()
    mock_detector.name = "detector_name"
    ai_care._tags = {"detector_tag": [mock_detector]}
    ai_care.ask = mock_ask
    ai_care.release_detector = mock_release_detector
    
    # Action
    ai_care.trigger(messages_list=[{"role": "ai_care", "content": "content"}])
    
    # Assert
    mock_ask.assert_called_with(
        chat_context=None,
        messages_list=[{"role": "ai_care", "content": "content"}],
        depth_left=1
    )
    assert not mock_release_detector.called

    # Action
    ai_care.trigger(tag="detector_tag")
    mock_release_detector.assert_called_with("detector_name")

def test_register_detector(ai_care: AICare):
    # Setup
    mock_detector = Mock()
    mock_detector.name = "mock_detector_name"
    mock_detector.tag = "mock_detector_tag"

    # Action
    ai_care.register_detector(mock_detector)

    # Assert
    assert mock_detector.ai_care == ai_care
    assert ai_care.detectors["mock_detector_name"] == mock_detector
    assert ai_care._tags["mock_detector_tag"] == [mock_detector]

def test_release_detector(ai_care: AICare):
    # Setup
    det_ann_called_list = []
    class TestDetector(Detector):
        def detect(self) -> bool:
            det_ann_called_list.append(self.annotation)
            return True
    test_detector1 = TestDetector(name="test_detector1", annotation="test_detector1_annotation")
    test_detector2 = TestDetector(name="test_detector2", annotation="test_detector2_annotation")
    test_detector3 = TestDetector(name="test_detector3", annotation="test_detector3_annotation")

    # Action
    ai_care.register_detector(test_detector1)
    ai_care.register_detector(test_detector2)
    ai_care.register_detector(test_detector3)
    ai_care.release_detector("test_detector1")
    ai_care.release_detector(["test_detector2", "test_detector3"])
    time.sleep(0.1)

    # Assert
    assert set(det_ann_called_list) == {"test_detector1_annotation", "test_detector2_annotation", "test_detector3_annotation"}

def test_register_sensor(ai_care: AICare):
    # Setup
    mock_sensor = Mock()
    mock_sensor.return_value = 10

    # Action
    ai_care.register_sensor(name="mock_sensor", function=mock_sensor, annotation="mock_sensor_annotation")

    # Assert
    assert ai_care.sensors["mock_sensor"] == {"name": "mock_sensor", "function": mock_sensor, "annotation": "mock_sensor_annotation"}

def test_get_sensor_data(ai_care: AICare):
    # Setup
    mock_sensor = Mock()
    mock_sensor.return_value = 10

    # Action
    ai_care.register_sensor(name="mock_sensor", function=mock_sensor, annotation="mock_sensor_annotation")

    # Assert
    assert ai_care.get_sensor_data("mock_sensor") == 10

def test_set_cyclic_detection(ai_care: AICare):
    # Setup
    mock_release_detector_method_1 = Mock()
    ai_care.release_detector = mock_release_detector_method_1

    # Action
    ai_care.set_cyclic_detection(detectors=["fake_release_detector"], interval_gen=(0.1 for _ in range(3)))
    time.sleep(0.6)

    # Assert
    assert mock_release_detector_method_1.called
    assert mock_release_detector_method_1.call_count == 3
    
    # Setup
    mock_release_detector_method_2 = Mock()
    ai_care.release_detector = mock_release_detector_method_2
    ai_care.to_llm_method = Mock()

    # Action
    with patch('ai_care.ai_care.parse_response') as mock_pares_response, patch('ai_care.ai_care.choice_execute'):
        mock_pares_response.return_value = ("01", "fake content")
        ai_care.set_cyclic_detection(detectors=["fake_release_detector"], interval_gen=(x for x in [0.1, 0.1, 0.2, 0.1, 0.1]))
        time.sleep(0.3)
        ai_care.trigger(messages_list=[{"role": "ai_care", "content": ""}])
        time.sleep(0.4)

    # Assert
    assert mock_release_detector_method_2.call_count == 2
