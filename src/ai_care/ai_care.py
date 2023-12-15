from __future__ import annotations
import itertools
import logging
import time
import threading
from abc import ABCMeta, abstractmethod
from threading import Thread
from typing import Callable, Any, Generator, TypedDict, Literal

from .abilities import Ability
from .choice_execute import choice_execute
from .parse_response import parse_response
from .render_prompt import render_basic_prompt


logger = logging.getLogger("ai_care")
ChatContext = Any


class AICare:

    def __init__(self) -> None:
        self.timers: dict[int, Timer] = {}
        self.detectors: dict[str, Detector] = {}
        self.sensors: dict[str, dict] = {}
        self.ability: Ability = Ability(self)
        self.chat_context: Any = None
        self.to_llm_method: (
            Callable[[ChatContext, list[AICareContext]], str] |
            Callable[[ChatContext, list[AICareContext]], Generator[str, None, None]]
        ) = self._fake_to_llm_method
        self.to_user_method: (
            Callable[[str], None] |
            Callable[[Generator[str, None, None]], None]
        ) = self._fake_to_user_method
        self.guide: str = ""
        self._unique_id = itertools.count(1)
        self._last_chat_time: float | None = None
        self._chat_intervals: list[float] = []
        self._tags: dict[str, list[Detector]] = {}
        self._config: dict[str, Any] = {"delay": 100, "ask_later_count_limit": 1, "ask_depth": 1, "n_chat_intervals": 20}
        self._ask_later_count_left = 1
        self._valid_msg_count: int = 0
        self._invalid_msg_count: int = 0
        self._stream_mode: bool = True
        self._ask_context: list[AICareContext] = []
    
    @property
    def health(self) -> float:
        return self._valid_msg_count / (self._valid_msg_count + self._invalid_msg_count)

    def reset(self) -> None:
        self._valid_msg_count = 0
        self._invalid_msg_count = 0
        self._last_chat_time = None
        self._chat_intervals = []
        self.clear_timer(clear_preserved=True)

    def set_guide(self, guide: str) -> None:
        """Set guidance information.

        This information can be any general type of information,
        such as descriptions of AI personality, descriptions of codes of conduct, etc.
        This information will be inserted into every round of dialogue between ai_care and the AI.

        Example:
            - You are a very considerate person who cares about others and is willing to initiate conversations.
            - You are someone who does not like to meddle in others' affairs, and you do not talk much unless necessary.
        """
        if not isinstance(guide, str):
            raise TypeError(f"Expected a guide of string type, but received a guide of type {type(guide)}.")
        self.guide = guide

    def _fake_to_llm_method(self, chat_context: ChatContext, to_llm_messages: list[AICareContext]) -> str:
        raise NotImplementedError("'to_llm_method' method has not been implemented yet.")
    
    def _fake_to_user_method(self, to_user_message: str) -> None:
        raise NotImplementedError("'to_user_method' method has not been implemented yet.")

    def register_to_llm_method(
        self,
        to_llm_method: Callable[[ChatContext, list[AICareContext]], str] | Callable[[ChatContext, list[AICareContext]], Generator[str, None, None]],
    ) -> None:
        """Register the method used by AICare to send message to llm."""
        self.to_llm_method = to_llm_method

    def register_to_user_method(
        self,
        to_user_method: Callable[[str], None] | Callable[[Generator[str, None, None]], None],
    ) -> None:
        """Register the method used by AICare to send message to user."""
        self.to_user_method = to_user_method

    def chat_update(self, chat_context: ChatContext) -> None:
        time_now = time.monotonic()
        if self._last_chat_time is not None:
            self._insert_chat_interval(time_now - self._last_chat_time)
        self._last_chat_time = time_now
        self.chat_context = chat_context
        self._ask_later_count_left = self._config["ask_later_count_limit"]
        self.clear_timer(clear_preserved=False)
        self._ask_context = []
        self.set_timer(
            interval=self._config["delay"],
            function=self.ask,
            kwargs={
                "messages_list": [
                    {
                        "role": "ai_care",
                        "content": render_basic_prompt(self),
                    }
                ],
            },
        )

    def _insert_chat_interval(self, interval: float) -> None:
        if len(self._chat_intervals) >= self._config["n_chat_intervals"]:
            self._chat_intervals.pop(0)
        self._chat_intervals.append(interval)

    def set_config(self, key: str, value: Any) -> None:
        # Valid check.
        if key not in {"delay", "ask_later_count_limit", "ask_depth", "n_chat_intervals"}:
            raise TypeError(f"AICare does not accept {key} as a config.")
        self._config[key] = value

    def set_timer(
        self,
        interval: float | int,
        function: Callable,
        args: tuple | None = None,
        kwargs: dict | None = None,
        preserve: bool = False,
    ) -> int:
        args = args or ()
        kwargs = kwargs or {}
        id = next(self._unique_id)
        timer = Timer(interval=interval, function=self._timer_wrap, args=(function, id, *args), kwargs=kwargs)
        timer._preserve_ = preserve
        timer.start()
        self.timers[id] = timer
        return id

    def clear_timer(self, clear_preserved: bool = True):
        keys = list(self.timers.keys())
        if clear_preserved is True:
            for key in keys:
                timer = self.timers.pop(key)
                timer.cancel()
        else:
            for key in keys:
                timer = self.timers[key]
                if timer._preserve_ is False:
                    timer.cancel()
                    self.timers.pop(key)

    def timer_cancel(self, id: int) -> None:
        timer = self.timers.pop(id, None)
        if timer is not None:
            timer.cancel()

    def _timer_wrap(self, function: Callable, id: int, *args, **kwargs) -> None:
        function(*args, **kwargs)
        try:
            del self.timers[id]
        except KeyError:
            pass

    def ask(
        self,
        messages_list: list[AICareContext],
        chat_context: ChatContext | None = None,
        depth_left: int | None = None
    ) -> None:
        if depth_left is None:
            depth_left = self._config["ask_depth"]
        assert depth_left is not None
        if depth_left < 0:
            return
        if chat_context is None:
            chat_context = self.chat_context
        self._ask_context.extend(messages_list)
        response = self.to_llm_method(chat_context, self._ask_context)
        self.clear_timer(clear_preserved=False)
        choice_code, content = parse_response(self, response)
        choice_execute(ai_care=self, choice_code=choice_code, content=content, depth_left=depth_left)

    def set_cyclic_detection(
        self,
        detectors: list[str],
        interval_gen: Generator[float, None, None],
        cancel_after_trigger_ask: bool = True
    ) -> None:
        def callback():
            for detector in detectors:
                self.release_detector(detector)
            try:
                self.set_timer(
                    interval=next(interval_gen),
                    function=callback,
                    preserve=not cancel_after_trigger_ask,
                )
            except StopIteration:
                pass
        try:
            self.set_timer(
                interval=next(interval_gen),
                function=callback,
                preserve=not cancel_after_trigger_ask,
            )
        except StopIteration:
            pass

    def trigger(
        self,
        messages_list: list[AICareContext] | None = None,
        tag: str | None = None,
        chat_context: ChatContext | None = None,
        depth_left: int = 1
    ) -> None:
        if messages_list:
            self.ask(chat_context=chat_context, messages_list=messages_list, depth_left=depth_left)
        if tag:
            for detector in self._tags[tag]:
                self.release_detector(detector.name)

    def register_detector(self, detector: Detector) -> None:
        if detector.name in self.detectors:
            raise ValueError("A detector with the same name already exists.")
        detector.ai_care = self
        self.detectors[detector.name] = detector
        tag = detector.tag
        if tag not in self._tags:
            self._tags[tag] = []
        self._tags[tag].append(detector)

    def release_detector(self, name: str | list[str]) -> None:
        if isinstance(name, list):
            names = name
        else:
            names = [name]
        for name in names:
            if name not in self.detectors:
                raise ValueError(f"There is no detector named {name}.")
            detector = self.detectors[name]
            Thread(target=detector.release).start()

    def register_sensor(self, name: str, function: Callable[[], Any], annotation: str) -> None:
        if name in self.sensors:
            raise ValueError(f"The sensor named {name} has already been registered.")
        self.sensors[name] = {"name": name, "function": function, "annotation": annotation}

    def get_sensor_data(self, name: str) -> Any:
        if name not in self.sensors:
            raise ValueError("No sensor named {name}.")
        sensor_function = self.sensors[name]["function"]
        data = sensor_function()
        return data


class Detector(metaclass=ABCMeta):
    def __init__(self, name: str, annotation: str, tag: str = '') -> None:
        self.name = name
        self.annotation = annotation
        self.tag = tag
        self.ai_care: AICare | None = None

    @abstractmethod
    def detect(self) -> bool:
        """Here, execute the detection logic and return whether it has triggered ai_care."""
        ...

    def release(self) -> None:
        self.detect()


class AICareContext(TypedDict):
    role: Literal["ai_care", "assistant"]
    content: str


class Timer(threading.Timer):
    def __init__(self, *args, preserve: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self._preserve_: bool = preserve
