"""Formatters for converting Pydantic schemas to Messenger API format.

Generic utilities for Messenger Send API message formatting.
"""

from app.integrations.messenger.types import (
    ButtonType,
    QuickReplyButton,
    TemplateButton,
    TemplateElement,
)


def format_quick_replies(replies: list[QuickReplyButton]) -> list[dict]:
    """Convert Pydantic QuickReplyButton objects to Messenger API format.

    Args:
        replies: List of QuickReplyButton instances

    Returns:
        List of dicts in Messenger API quick_reply format
    """
    formatted = []
    for qr in replies:
        formatted_reply = {
            "content_type": qr.content_type.value,
            "title": qr.title,
            "payload": qr.payload,
        }
        if qr.image_url:
            formatted_reply["image_url"] = qr.image_url
        formatted.append(formatted_reply)
    return formatted


def format_template_buttons(buttons: list[TemplateButton]) -> list[dict]:
    """Convert Pydantic TemplateButton objects to Messenger API format.

    Args:
        buttons: List of TemplateButton instances

    Returns:
        List of dicts in Messenger API button format
    """
    formatted = []
    for btn in buttons:
        if btn.type == ButtonType.WEB_URL:
            formatted.append(
                {
                    "type": "web_url",
                    "title": btn.title,
                    "url": btn.url,
                }
            )
        elif btn.type == ButtonType.POSTBACK:
            formatted.append(
                {
                    "type": "postback",
                    "title": btn.title,
                    "payload": btn.payload,
                }
            )
    return formatted


def format_template_elements(elements: list[TemplateElement]) -> list[dict]:
    """Convert Pydantic TemplateElement objects to Messenger API format.

    Args:
        elements: List of TemplateElement instances

    Returns:
        List of dicts in Messenger API generic template element format
    """
    formatted = []
    for elem in elements:
        formatted_elem = {"title": elem.title}

        if elem.subtitle:
            formatted_elem["subtitle"] = elem.subtitle
        if elem.image_url:
            formatted_elem["image_url"] = elem.image_url
        if elem.buttons:
            formatted_elem["buttons"] = format_template_buttons(elem.buttons)

        formatted.append(formatted_elem)
    return formatted
