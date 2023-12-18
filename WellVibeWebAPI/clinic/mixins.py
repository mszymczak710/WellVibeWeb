import logging

from django.contrib.admin import ModelAdmin
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from rest_framework import serializers

# Configure a logger for this module
logger = logging.getLogger(__name__)


class MailSendingMixin:
    """
    Mixin to add email sending capability.

    This mixin provides a method to send emails using a template and context.
    It also handles and logs exceptions that may occur during the email sending process.
    """

    def send_email(self, subject, template_name, context, to_email):
        """
        Renders an email template with context and sends an email.

        Args:
            subject (str): The subject of the email.
            template_name (str): The path to the email template.
            context (dict): The context to render the template with.
            to_email (str): The recipient's email address.

        Raises:
            serializers.ValidationError: If there is an error sending the email.
        """
        message = render_to_string(template_name, context)
        email_message = EmailMessage(subject, message, to=[to_email])
        try:
            email_message.send()
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            raise serializers.ValidationError(_("Error sending email."))


class FullnameAdminMixin(ModelAdmin):
    """
    Mixin to add full name display to Django admin for related user objects.

    This mixin provides methods to access the first name and last name of a related user object,
    and specifies how these fields should be ordered and described in the admin interface.
    """

    def user_first_name(self, obj):
        """
        Retrieve the first name of the user related to the object.

        Args:
            obj: The object that has a related user.

        Returns:
            str: The first name of the related user.
        """
        return obj.user.first_name

    user_first_name.admin_order_field = (
        "user__first_name"  # Allows column order sorting
    )
    user_first_name.short_description = _("first name")  # Column header

    def user_last_name(self, obj):
        """
        Retrieve the last name of the user related to the object.

        Args:
            obj: The object that has a related user.

        Returns:
            str: The last name of the related user.
        """
        return obj.user.last_name

    user_last_name.admin_order_field = (
        "user__last_name"  # Allows column order sorting
    )
    user_last_name.short_description = _("last name")  # Column header
