from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """
    Authentication backend that allows for authentication using an email address.

    Inherits from ModelBackend and overrides the authenticate method to allow
    users to log in using their email address instead of a username.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user based on email address as the user name.
        """
        User = get_user_model()
        try:
            # Try to fetch the user by searching the email field in the user model.
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            # If the user does not exist, return None.
            return None
        else:
            # Check if the password is correct and the user is allowed to authenticate.
            if user.check_password(password) and self.user_can_authenticate(
                user
            ):
                return user
        # If the password check fails, return None.
        return None
