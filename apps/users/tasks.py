# Python modules
from typing import Any

# Django + Third party modules
from celery import shared_task

# Project modules
from .tools import send_registration_email


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_welcome_email(id: int, subject: str, context: dict[str, Any]) -> None:
    """Sends a welcome email to a new user."""
    from apps.users.models import CustomUser

    user = CustomUser.objects.filter(id=id).first()
    if user:
        send_registration_email(
            subject=subject,
            recipient_list=[user.email],
            context=context,
            html_template_name="mails/welcome.html",
            language=user.preffered_language,
        )
