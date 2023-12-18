from __future__ import annotations
import inspect
import logging
from enum import Enum, unique
from typing import TYPE_CHECKING, Generator


if TYPE_CHECKING:
    from .ai_care import AICare


logger = logging.getLogger("ai_care")


@unique
class Choice(Enum):
    ERROR = '00'
    STAY_SILENT = '01'
    SPEAK_NOW = '02'
    SPEAK_AFTER = '03'
    DETECT_ENV = '04'
    RELEASE_DETECTOR = '05'
    ASK_LATER = '06'
    CYCLIC_DETECTION = '07'


def _ability(description: str):
    def decorator(func):
        func._ability_ = True
        func._ability_description_ = description
        if not hasattr(func, "_ability_parameters_"):
            func._ability_parameters_ = []
        return func
    return decorator

def _ability_parameter(
    *,
    name: str,
    description: str,
    default_value: str = "",
    param_type: str = "string",
    required: bool = True
):
    """
    Decorator for ability parameters.

    Args:
        name: The name of the ability parameter
        description: The description of the ability parameter
        default_value: The default value of the ability parameter
        type: The type of the ability parameter
        required: Whether the ability parameter is required
    """

    def decorator(func):
        if not hasattr(func, "_ability_parameters_"):
            func._ability_parameters_ = []

        func._ability_parameters_.append(
            {
                "name": name,
                "description": description,
                "default_value": default_value,
                "param_type": param_type,
                "required": required,
            }
        )
        return func

    return decorator

def _auto_depth(depth_param_name: str = "_depth_left"):
    def decorator(func):
        func._auto_depth_ = True
        func._depth_param_name_ = depth_param_name
        return func
    return decorator
    

class Ability:
    def __init__(self, ai_care: AICare):
        self.ai_care = ai_care
        self.abilities: dict = {}
        self._register_abilities()

    def _register_abilities(self) -> None:
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if getattr(method, '_ability_', False):
                self.abilities[name] = method

    @_ability(
        description="Remain silent.",
    )
    def stay_silent(self) -> None:
        return
    
    @_ability(
        description="Speak to the user right now.",
    )
    @_ability_parameter(
        name="content",
        description="The content you want to say.",
    )
    def speak_now(self, content: str | Generator[str, None, None]) -> None:
        self.ai_care.to_user_method(content)

    @_ability(
        description=(
            "Set a message to be delivered to the user after a certain period of time. "
            "This choice means you decide to observe for a duration, and if the user does "
            "not speak to you during this time, you will then convey the message content you have set. "
            "However, if the user speaks to you within this time frame, the operation will automatically "
            "be cancelled. This option is recommended."
        )
    )
    @_ability_parameter(
        name="delay",
        description="Set how long until your message is sent. Unit in seconds.",
    )
    @_ability_parameter(
        name="message",
        description="Set what you want to say to the user after a certain period of time.",
    )
    def speak_after(self, delay: float | int, message: str) -> None:
        if self.ai_care._stream_mode is True:
            message_wrap = (string for string in [message])
        else:
            message_wrap = message
        self.ai_care.set_timer(interval=delay, function=self.ai_care.to_user_method, args=(message_wrap,))
    
    @_ability(
        description=(
            "Detect environmental conditions. This choice means that you decide to first obtain the results "
            "from the sensors, observe the environmental situation, and then decide what to choose based on "
            "this information. You can only choose which sensors to use from the list of available sensors."
        ),
    )
    @_ability_parameter(
        name="delay",
        description="Set how long to wait before using sensors to obtain readings. Unit in seconds.",
    )
    @_ability_parameter(
        name="sensors",
        description="The list of names of the sensors to be used.",
        param_type="list[str]",
    )
    @_auto_depth(depth_param_name="_depth_left")
    def detect_env(self, delay: float | int, sensors: list[str], _depth_left: int) -> None:
        def detect_env_callback(sensors_list: list[str]):
            sensor_data = {}
            for sensor in sensors_list:
                data = self.ai_care.get_sensor_data(sensor)
                sensor_data[sensor] = data
            self.ai_care.ask(
                messages_list=[
                    {
                        "role": "ai_care",
                        "content": f"The results of the sensor are as follows: {str(sensor_data)}.",
                    },
                ],
                depth_left = _depth_left - 1,
            )
        not_existed_sensors_set = set(sensors) - set(self.ai_care.sensors)
        if not_existed_sensors_set:
            self.ai_care.ask(
                messages_list=[
                    {
                        "role": "ai_care",
                        "content": f"There are no {str(not_existed_sensors_set)} sensor. Please use the correct sensor name.",
                    }
                ],
                depth_left = _depth_left - 1,
            )
            return
        self.ai_care.set_timer(
            interval=delay,
            function=detect_env_callback,
            args=(sensors,),
        )

    @_ability(
        description=(
            "Release detectors. This option means you forego making an active choice and instead release "
            "some detectors, which will automatically report back to you and ask for your decision when "
            "specific conditions are met. You can only choose which detectors to use from the list of "
            "available detectors."
        ),
    )
    @_ability_parameter(
        name="delay",
        description="Set the time in seconds before releasing the detectors.",
    )
    @_ability_parameter(
        name="detectors",
        description="The list of names of the detectors to be released.",
    )
    @_auto_depth(depth_param_name="_depth_left")
    def release_detector(self, delay: int | float, detectors: list[str], _depth_left: int) -> None:
        def release_detector_callback(detectors_list: list[str]):
            self.ai_care.release_detector(detectors_list)
        not_existed_detectors_set = set(detectors) - set(self.ai_care.detectors)
        if not_existed_detectors_set:
            self.ai_care.ask(
                messages_list=[
                    {
                        "role": "ai_care",
                        "content": f"There are no {str(not_existed_detectors_set)} detector. Please use the correct detector name.",
                    }
                ],
                depth_left = _depth_left - 1,
            )
            return
        self.ai_care.set_timer(interval=delay, function=release_detector_callback, args=(detectors,))

    @_ability(
        description=(
            "Ask again after a while. This choice means that you do not want to make a decision right now, "
            "and you would like Aicarey to ask you again later."
        ),
    )
    @_ability_parameter(
        name="delay",
        description="Set how long to wait before asking you again, in seconds.",
    )
    @_auto_depth(depth_param_name="_depth_left")
    def ask_later(self, delay: int | float, _depth_left: int) -> None:
        if self.ai_care._ask_later_count_left <= 0:
            return
        self.ai_care._ask_later_count_left -= 1
        self.ai_care.set_timer(
            interval=delay,
            function=self.ai_care.ask,
            kwargs={
                "messages_list": [
                    {
                        "role": "ai_care",
                        "content": (
                            f"{delay} senconds ago, you asked me to inquire later, "
                            f"and now {delay} seconds have passed. Please make a choice."
                        )
                    }
                ],
                "depth_left": _depth_left - 1,
            },
        )

    @_ability(
        description=(
            "Cycle release of detectors. This option means that you forgo making an active choice "
            "and instead continuously release some detectors, which will automatically report back "
            "to you and ask for your decision when specific conditions are met. The detectors you "
            "select will be released periodically at set time intervals until the next conversation "
            "is initiated. All chosen detectors will be released in each cycle."
        ),
    )
    @_ability_parameter(
        name="interval",
        description="Set the time interval between each release of the detectors. Unit in seconds",
    )
    @_ability_parameter(
        name="detectors",
        description="The list of names of the detectors to be released.",
    )
    @_auto_depth(depth_param_name="_depth_left")
    def cyclic_detection(self, interval: int | float, detectors: list[str], _depth_left) -> None:
        not_existed_detectors_set = set(detectors) - set(self.ai_care.detectors)
        if not_existed_detectors_set:
            self.ai_care.ask(
                messages_list=[
                    {
                        "role": "ai_care",
                        "content": f"There are no {str(not_existed_detectors_set)} detector. Please use the correct detector name.",
                    }
                ],
                depth_left = _depth_left - 1,
            )
            return
        def repeat_interval(interval: float):
            while True:
                yield interval
        self.ai_care.set_cyclic_detection(
            detectors=detectors,
            interval_gen=repeat_interval(float(interval)),
            cancel_after_trigger_ask=True
        )
