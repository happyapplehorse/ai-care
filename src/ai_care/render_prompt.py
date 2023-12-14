from __future__ import annotations
import textwrap
import time
from typing import TYPE_CHECKING

from .abilities import Choice


if TYPE_CHECKING:
    from .ai_care import AICare


def render_basic_prompt(
    ai_care: AICare,
    inactive_abilities_list: list[Choice] | None = None,
    inactive_sensors_list: list[str] | None = None,
    inactive_detectors_list: list[str] | None = None,
) -> str:
    inactive_abilities_set = set() if inactive_abilities_list is None else set(inactive_abilities_list)
    inactive_sensors_set = set() if inactive_sensors_list is None else set(inactive_sensors_list)
    inactive_detectors_set = set() if inactive_detectors_list is None else set(inactive_detectors_list)
    if ai_care._ask_later_count_left <= 0:
        inactive_abilities_set.add(Choice.ASK_LATER)
    
    abilities_dict = ai_care.ability.abilities
    
    assert ai_care._last_chat_time is not None

    prompt = textwrap.dedent(
        f"""
        I am a program, and my name is Aicarey.
        You can see your conversation history with the user in the previous messages.
        This message is sent by me. Please continue to focus on the user and do not attempt to converse with me.

        When replying to this message, you must follow the rules below:
        ========================RESPONSE RULES=======================
        1. Start with eight characters followed by an English colon.
        The first two characters of these eight must be 'AA', the third and fourth must be '00',
        the fifth and sixth are the code of your choice.
        The seventh and eighth characters should repeat the fifth and sixth characters.
        2. After the colon is the content corresponding to the chosen option.
        If it involves a function call, this part of the content must be in the format of a JSON string.
        =============================================================

        Here are the choices you can make:
        ===========================CHOICES===========================
        {
            ''.join(
                _render_ability_description(ability_method)
                for ability_method in abilities_dict.values()
                if ability_method not in inactive_abilities_set
            )
        }
        =============================================================
        You must choose one of the options provided above as your reply.
        
        Response Examples:
            If you want to remain silent: AA000101:
            If you want to say to the user: AA000202: [Your content here]
            If you decide to ask the user what they are doing if they haven't spoken to you in a minute: AA000303: {{"delay":60, "message":"What are you doing?"}}

        ===========================SENSORS===========================
        Sensors list:
        {
            str(
                [
                    {"sensor_name": sensor["name"], "sensor_description": sensor["annotation"]}
                    for sensor in ai_care.sensors.values()
                    if sensor not in inactive_sensors_set
                ]
            )
        }
        =============================================================
        
        ==========================DETECTORS==========================
        Detectors list:
        {
            str(
                [
                    {"detector_name": detector.name, "detector_description": detector.annotation}
                    for detector in ai_care.detectors.values()
                    if detector not in inactive_detectors_set
                ]
            )
        }
        =============================================================
        
        ============================FACTS============================
        The intervals of the last {len(ai_care._chat_intervals)} times the user conversed with you are recorded in the following list (unit in seconds):
        {str(ai_care._chat_intervals)}
        It has been {time.monotonic() - ai_care._last_chat_time} seconds since the last time the user spoke with you.
        
        {ai_care.guide}
        =============================================================
        """
    )
    return prompt

def _render_ability_description(ability_method) -> str:
    choice = Choice[ability_method.__name__.upper()]
    content_string = "The content you want to say\n" if choice == Choice.SPEAK_NOW \
        else "Provide the values of the following parameters in JSON format\n" if ability_method._ability_parameters_ \
        else "Empty\n"
    for param_dict in ability_method._ability_parameters_:
        content_string += f"    Parameter name: {param_dict['name']}\n"
        content_string += f"    Parameter description: {param_dict['description']}\n"
        content_string += f"    Parameter type: {param_dict['param_type']}\n"
        if param_dict["required"] is False:
            content_string += f"    This parameter is optional, with a default value: {param_dict['default_value']}\n\n"
        else:
            content_string += f"    This parameter must be provided\n\n"
    prompt = (
        "\n"
        f"Choice code: {choice.value}\n"
        f"Choice description: {ability_method._ability_description_}\n"
        f"Choice content: {content_string}"
    )
    return prompt
