import json
import logging
from typing import TYPE_CHECKING, Generator

from .abilities import Choice


logger = logging.getLogger("ai_care")


if TYPE_CHECKING:
    from .ai_care import AiCare


def choice_execute(ai_care: AiCare, choice_code: str, content: str | Generator[str, None, None], depth_left: int) -> None:
    try:
        choice = Choice(choice_code)
    except ValueError as e:
        logger.warning(f"Invalid choice {choice_code}.")
        ai_care.ask(
            messages_list=[
                {
                    "role": "assistant",
                    "content": f"AA00{choice_code}{choice_code}:{content}",
                },
                {
                    "role": "ai_care",
                    "content": f"Your choice code {choice_code} is not correct. Please make a correct choice again.",
                },
            ],
            depth_left = depth_left - 1,
        )
        return

    if choice == Choice.ERROR:
        ai_care.ask(messages_list=[], depth_left = depth_left - 1)
        return

    if isinstance(content, str):
        ai_care._ask_context.append(
            {
                "role": "assistant",
                "content": f"AA00{choice_code}{choice_code}:{content}",
            }
        )
    else:
        # This case has been handled in parse_response.
        pass

    if choice not in {Choice.SPEAK_NOW, Choice.STAY_SILENT}:
        assert isinstance(content, str)
        try:
            params = json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to correctly parse the parameter. Parameter json string: {content}. Error: {e}.")
            ai_care.ask(
                messages_list=[
                    {
                        "role": "ai_care",
                        "content": (
                            "Failed to correctly parse the parameter. "
                            "Please send the correct parameters in JSON format, "
                            "or make a choice again."
                        ),
                    },
                ],
                depth_left = depth_left - 1,
            )
            return
        if not isinstance(params, dict):
            ai_care.ask(
                messages_list=[
                    {
                        "role": "ai_care",
                        "content": (
                            "The parameters should be a dictionary in JSON format."
                            "Please send the correct parameters in JSON format, or make a choice again."
                        ),
                    },
                ],
                depth_left = depth_left - 1,
            )
    else:
        params = {"content": content}

    ability_method = ai_care.ability.abilities[choice.name.lower()]
    ability_params = {}
    for param in ability_method._ability_parameters_:
        default_value = param["default_value"]
        if param["required"] is False:
            ability_params[param["name"]] = default_value
    ability_params.update(params)
    if getattr(ability_method, "_auto_depth_", False):
        ability_params[ability_method._depth_param_name_] = depth_left

    needed_params_set = {param["name"] for param in ability_method._ability_parameters_}
    missing_params_set = needed_params_set - set(ability_params.keys())

    if missing_params_set:
        ai_care.ask(
            messages_list=[
                {
                    "role": "ai_care",
                    "content": (
                        f"You did not provide the following parameters: {str(missing_params_set)} ."
                        "Please send the correct parameters in JSON format, or make a choice again."
                    ),
                },
            ],
            depth_left = depth_left - 1
        )
        return

    ability_method(**ability_params)
