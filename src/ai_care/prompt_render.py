import time
from typing import TYPE_CHECKING

from .abilities import Choice


if TYPE_CHECKING:
    from .ai_care import AiCare


def basic_prompt_render(ai_care: AiCare) -> str:
    abilities_dict = ai_care.ability.abilities
    prompt = f"""
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
        {''.join(_render_ability_description(ability_method) for ability_method in abilities_dict.values())}
        =============================================================
        You must choose one of the options provided above as your reply.
        
        Response Examples:
            If you want to remain silent: AA000101:
            If you want to say to the user: AA000202: [Your content here]
            If you decide to ask the user what they are doing if they haven't spoken to you in a minute: AA000303: {"delay":60, "message":"What are you doing?"}

        ===========================SENSORS===========================
        Sensors list:
        {str([{"sensor_name": sensor["name"], "sensor_description": sensor["annotation"]} for sensor in ai_care.sensors.values()])}
        =============================================================
        
        ==========================DETECTORS==========================
        Detectors list:
        {str([{"detector_name": detector.name, "detector_description": detector.annotation} for detector in ai_care.detectors.values()])}
        =============================================================
        
        ============================FACTS============================
        The intervals of the last {len(ai_care._chat_intervals)} times the user conversed with you are recorded in the following list (unit in seconds):
        {str(ai_care._chat_intervals)}
        It has been {time.time.monotonic() - ai_care._last_chat_time} seconds since the last time the user spoke with you.
        
        {ai_care.guide}
        =============================================================
    """
    
    return prompt

def _render_ability_description(ability_method) -> str:
    content_string = ""
    for param_dict in ability_method._ability_description_:
        content_string += f"Parameter name: {param_dict['name']}\n"
        content_string += f"Parameter type: {param_dict['param_type']}\n"
        content_string += f"Parameter description: {param_dict['description']}\n"
        if param_dict["required"] is False:
            content_string += f"This parameter is optional, with a default value of {param_dict['default_value']}\n"
        else:
            content_string += f"This parameter must be provided\n"
    content_string = content_string or "None"
    prompt = (
        f"Choice code: {Choice[ability_method.__name__.upper()].value}\n"
        f"Description: {ability_method._ability_description_}\n"
        f"Content: {content_string}"
    )
    return prompt
