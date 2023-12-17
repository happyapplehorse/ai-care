from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Generator, cast

from .abilities import Choice


if TYPE_CHECKING:
    from .ai_care import AICare


logger = logging.getLogger("ai_care")


def parse_response(
    ai_care: AICare,
    response: str | Generator[str, None, None],
) -> tuple[str, str | Generator[str, None, None]]:
    choice_code = ""
    content = ""
    if isinstance(response, str):
        ai_care._stream_mode = False
        prefix, content = _extract_info(response)
        if not all(prefix):
            return '00', ''
        choice_code = prefix[2]
        check_valid = prefix[3]
        if choice_code == check_valid:
            ai_care._valid_msg_count += 1
        else:
            ai_care._invalid_msg_count += 1
        assert isinstance(choice_code, str)
        return choice_code, content or ""
    elif isinstance(response, Generator):
        ai_care._stream_mode = True
        buffer = ""
        first_item = ""
        chunk_list = []
        found_choice = False
        prefix = (None, None, None, None)
        choice = Choice.ERROR
        for chunk in response:
            buffer += chunk
            if not found_choice:
                prefix, content = _extract_info(buffer)
            if all(prefix) and len(buffer) >= 9 and not found_choice:
                choice_code = prefix[2]
                check_valid = prefix[3]
                if choice_code == check_valid:
                    ai_care._valid_msg_count += 1
                else:
                    ai_care._invalid_msg_count += 1
                try:
                    choice = Choice(choice_code)
                except ValueError as e:
                    logger.warning(f"Invalid choice {choice_code}. Error: {e}")
                    assert isinstance(choice_code, str)
                    return choice_code, ''
                found_choice = True
                if choice == Choice.SPEAK_NOW:
                    first_item = buffer[9:]
                    break
                chunk_list.append(buffer[9:])
                continue
            if found_choice:
                chunk_list.append(chunk)
        if found_choice is False:
            return '00', ''
        prefix = cast(tuple[str, str, str, str], prefix)
        if choice == Choice.SPEAK_NOW:
            def response_content_gen():
                gen_content_record = []
                yield first_item
                gen_content_record.append(first_item)
                for item in response:
                    yield item
                    gen_content_record.append(item)
                ai_care._ask_context.append(
                    {
                        "role": "ai_care",
                        "content": ''.join(gen_content_record),
                    }
                )
            return choice.value, response_content_gen()
        else:
            return choice.value, ''.join(chunk_list)
    else:
        assert False, "The response must be str or a generator."

def _extract_info(s: str) -> tuple[tuple[str | None, str | None, str | None, str | None], str | None]:
    """Parse a given string.

    It extracts two-letter groups from the first eight characters
    and the remainder of the string after the ninth character. If a group is not complete (less than two characters),
    it is set to None.

    Parameters:
    s (str): The string to be parsed.

    Returns:
    tuple: A tuple containing a tuple of four two-letter groups and the remainder of the string.
    """
    # Extract the first eight characters and split them into four groups
    groups = [s[i:i+2] if len(s[i:i+2]) == 2 else None for i in range(0, 8, 2)]

    # Extract the remainder of the string after the ninth character
    remainder = s[9:] if len(s) > 9 else None

    return (tuple(groups), remainder)
