from typing import Any, Optional

from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.translation import override


def send_registration_email(
    subject: str,
    recipient_list: list[str,],
    context: dict[str, Any],
    html_template_name: str,
    text_template_name: str,
    language: str,
    from_email: Optional[str] = None,
) -> None:
    """Sends an email to a new user."""
    with override(language=language):
        subject: str = _(subject)
        html_content: str = render_to_string(html_template_name, context)
        text_content: str = (
            render_to_string(text_template_name, context)
            if text_template_name
            else strip_tags(html_content)
        )
        text_content = _(text_content)
        msg: EmailMultiAlternatives = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
