from datetime import datetime

from markupsafe import Markup
from sqlalchemy.orm import InstrumentedAttribute, selectinload
from sqladmin import ModelView
from starlette.requests import Request

from app.models import Conversation, Message, User
from app.models.example import Example


# Common formatter functions
def format_datetime(dt: datetime | None) -> str | None:
    """Format datetime to readable string."""
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None


def format_user_name_email(user: User | None) -> str | None:
    """Format user as 'Name (Email)'."""
    return f"{user.name} ({user.email})" if user else None


def format_message_box(content: str, user: User | None = None) -> str:
    """Format a single message as HTML box."""
    if user:
        return (
            f"<div style='margin: 8px 0; padding: 12px; background: #f8f9fa; "
            f"border-left: 3px solid #0066cc; border-radius: 4px;'>"
            f"<div style='font-size: 0.9em; color: #666; margin-bottom: 6px;'>"
            f"<strong>{user.name if user else 'N/A'}</strong> "
            f"<span style='color: #999;'>({user.email if user else 'N/A'})</span>"
            f"</div>"
            f"<div style='color: #333;'>{content}</div>"
            f"</div>"
        )
    return (
        f"<div style='margin: 8px 0; padding: 12px; background: #f8f9fa; "
        f"border-left: 3px solid #0066cc; border-radius: 4px; color: #333;'>"
        f"{content}"
        f"</div>"
    )


class BaseAdmin(ModelView):
    """Base admin view with common configuration."""

    # Pagination - shared across all views
    page_size = 25
    page_size_options = [10, 25, 50, 100]

    def _build_details_query(self, request: Request, *options):
        """Helper to build details query with eager loaded relationships.

        Args:
            request: Starlette request object
            *options: SQLAlchemy loader options (can be relationship attributes or
                     already-configured selectinload chains)

        Returns:
            SQLAlchemy select statement with eager loading
        """
        pk = request.path_params["pk"]
        stmt = self._stmt_by_identifier(pk)

        if options:
            # Convert plain attributes to selectinload, pass through existing options
            processed_options = []
            for opt in options:
                # If it's a relationship attribute, wrap in selectinload
                if isinstance(opt, InstrumentedAttribute):
                    processed_options.append(selectinload(opt))
                else:
                    # Otherwise it's already a loader option, use as-is
                    processed_options.append(opt)

            stmt = stmt.options(*processed_options)

        return stmt


class ExampleAdmin(BaseAdmin, model=Example):
    """Admin view for Example model."""

    name = "Example"
    name_plural = "Examples"
    icon = "fa-solid fa-list"

    # List page configuration
    column_list = [Example.id, Example.name, Example.description, Example.created_at]
    column_searchable_list = [Example.name, Example.description]
    column_sortable_list = [Example.id, Example.name, Example.created_at]
    column_default_sort = [(Example.created_at, True)]

    # Form configuration
    form_columns = [Example.name, Example.description]

    # Details page
    column_details_list = [
        Example.id,
        Example.name,
        Example.description,
        Example.created_at,
        Example.updated_at,
    ]


class UserAdmin(BaseAdmin, model=User):
    """Admin view for User model."""

    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"

    # List page configuration
    column_list = [User.email, User.name, User.role, User.created_at]
    column_searchable_list = [User.email, User.name]
    column_sortable_list = [User.email, User.name, User.role, User.created_at]
    column_default_sort = [(User.created_at, True)]

    # Form configuration
    form_columns = [User.email, User.name, User.role, User.profile]

    # Details page
    column_details_list = [
        User.id,
        User.email,
        User.name,
        User.role,
        User.profile,
        User.created_at,
        User.updated_at,
        "messages_display",
    ]

    column_formatters = {
        User.created_at: lambda m, _: format_datetime(m.created_at),
    }

    column_formatters_detail = {
        "messages_display": lambda m, _: Markup(
            "".join([format_message_box(msg.content) for msg in m.messages])
        )
        if m.messages
        else "No messages",
        User.created_at: lambda m, _: format_datetime(m.created_at),
        User.updated_at: lambda m, _: format_datetime(m.updated_at),
    }

    column_labels = {"messages_display": "Messages"}

    def details_query(self, request: Request):
        """Override to eagerly load nested relationships."""
        return self._build_details_query(request, User.messages)


class ConversationAdmin(BaseAdmin, model=Conversation):
    """Admin view for Conversation model."""

    name = "Conversation"
    name_plural = "Conversations"
    icon = "fa-solid fa-comments"

    # List page configuration
    column_list = [
        Conversation.title,
        Conversation.user,
        Conversation.created_at,
    ]
    column_searchable_list = [Conversation.title]
    column_sortable_list = [Conversation.title, Conversation.created_at]
    column_default_sort = [(Conversation.created_at, True)]

    # Form configuration
    form_columns = [Conversation.title, Conversation.user_id]

    # Details page - show messages and user
    column_details_list = [
        Conversation.id,
        Conversation.title,
        Conversation.user,
        "messages_display",
        Conversation.created_at,
        Conversation.updated_at,
    ]

    # Custom formatters for cleaner display
    column_formatters = {
        Conversation.user: lambda m, _: format_user_name_email(m.user),
        Conversation.created_at: lambda m, _: format_datetime(m.created_at),
    }

    column_formatters_detail = {
        Conversation.user: lambda m, _: format_user_name_email(m.user),
        "messages_display": lambda m, _: Markup(
            "".join([format_message_box(msg.content, msg.user) for msg in m.messages])
        )
        if m.messages
        else "No messages",
        Conversation.created_at: lambda m, _: format_datetime(m.created_at),
        Conversation.updated_at: lambda m, _: format_datetime(m.updated_at),
    }

    column_labels = {"messages_display": "Messages"}

    def details_query(self, request: Request):
        """Override to eagerly load nested relationships."""
        return self._build_details_query(
            request,
            Conversation.user,
            selectinload(Conversation.messages).selectinload(Message.user),
        )


class MessageAdmin(BaseAdmin, model=Message):
    """Admin view for Message model."""

    name = "Message"
    name_plural = "Messages"
    icon = "fa-solid fa-message"

    # List page configuration
    column_list = [
        Message.user,
        Message.content,
        Message.created_at,
    ]
    column_searchable_list = [Message.content]
    column_sortable_list = [Message.created_at]
    column_default_sort = [(Message.created_at, True)]

    # Form configuration
    form_columns = [Message.conversation_id, Message.user_id, Message.content]

    # Details page
    column_details_list = [
        Message.id,
        Message.conversation,
        Message.user,
        Message.content,
        Message.created_at,
        Message.updated_at,
    ]

    # Custom formatters for cleaner display
    column_formatters = {
        Message.user: lambda m, _: format_user_name_email(m.user),
        Message.created_at: lambda m, _: format_datetime(m.created_at),
    }

    column_formatters_detail = {
        Message.conversation: lambda m,
        _: f"{m.conversation.title} ({m.conversation.id})" if m.conversation else None,
        Message.user: lambda m, _: format_user_name_email(m.user),
        Message.created_at: lambda m, _: format_datetime(m.created_at),
        Message.updated_at: lambda m, _: format_datetime(m.updated_at),
    }

    def details_query(self, request: Request):
        """Override to eagerly load nested relationships."""
        return self._build_details_query(request, Message.user, Message.conversation)
