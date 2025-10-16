"""Message formatting utilities for storing rich messages as readable text."""

from typing import Any


def format_response_for_storage(response: Any) -> str:
    """Format multi-message response for database storage.

    Works with any response object that has a .messages attribute following
    the MultiMessageResponseProtocol (duck typing).

    Args:
        response: Response object with .messages attribute containing message components

    Returns:
        Human-readable formatted string combining all messages

    Example:
        >>> response = AIResponse(messages=[...])
        >>> formatted = format_response_for_storage(response)
        "Hello! [Options: Location A, Location B]"
    """
    from app.integrations.messenger.types import MessageType

    formatted_parts = []

    for msg in response.messages:
        if msg.type == MessageType.TEXT:
            formatted_parts.append(msg.text)

        elif msg.type == MessageType.QUICK_REPLY:
            formatted = format_messenger_message(
                message_type="quick_replies",
                text=msg.text,
                quick_replies=[{"title": qr.title} for qr in msg.quick_replies],
            )
            formatted_parts.append(formatted)

        elif msg.type == MessageType.TEMPLATE:
            formatted = format_messenger_message(
                message_type="generic_template",
                elements=[{"title": elem.title} for elem in msg.template_elements],
            )
            formatted_parts.append(formatted)

    return "\n\n".join(formatted_parts)


def format_messenger_message(
    message_type: str, text: str | None = None, **kwargs
) -> str:
    """
    Format Messenger message data into human-readable text for database storage.

    Converts rich message types (quick_replies, generic_template, postback)
    into descriptive text that provides context for LLM conversation history.

    Args:
        message_type: Type of message ("text", "quick_replies", "generic_template", "postback")
        text: Main message text (for text and quick_replies types)
        **kwargs: Type-specific data (quick_replies, elements, payload, title)

    Returns:
        Formatted string for content field

    Examples:
        >>> format_messenger_message("text", text="Hello!")
        "Hello!"

        >>> format_messenger_message("quick_replies", text="Choose color",
        ...     quick_replies=[{"title": "Red"}, {"title": "Blue"}])
        "Choose color [Options: Red, Blue]"

        >>> format_messenger_message("generic_template",
        ...     elements=[{"title": "Product 1"}, {"title": "Product 2"}])
        "[Sent 2 cards: Product 1, Product 2]"

        >>> format_messenger_message("postback", title="Buy Now", payload="PRODUCT_123")
        "[User clicked: Buy Now - PRODUCT_123]"
    """
    if message_type == "text":
        return text or ""

    if message_type == "quick_replies":
        quick_replies = kwargs.get("quick_replies", [])
        options = ", ".join(
            qr.get("title", "") for qr in quick_replies if qr.get("title")
        )
        return f"{text} [Options: {options}]" if options else text or ""

    if message_type == "generic_template":
        elements = kwargs.get("elements", [])
        count = len(elements)
        titles = ", ".join(elem.get("title", "") for elem in elements[:3])
        if count > 3:
            titles += f", ... ({count - 3} more)"
        card_label = "card" if count == 1 else "cards"
        return f"[Sent {count} {card_label}: {titles}]"

    if message_type == "postback":
        title = kwargs.get("title", "")
        payload = kwargs.get("payload", "")
        return f"[User clicked: {title} - {payload}]"

    return text or ""
