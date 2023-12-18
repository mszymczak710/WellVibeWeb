from django.urls import path, re_path

from clinic.auth.views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    RegisterView,
    ResetPasswordConfirmView,
    ResetPasswordView,
    VerifyEmailView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "verify-email/<str:uidb64>/<str:token>/",
        VerifyEmailView.as_view(),
        name="verify-email",
    ),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path(
        "reset-password/",
        ResetPasswordView.as_view(),
        name="reset-password",
    ),
    re_path(
        r"^reset-password-confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,40})/$",
        ResetPasswordConfirmView.as_view(),
        name="reset-password-confirm",
    ),
    path(
        "change-password/",
        ChangePasswordView.as_view(),
        name="change-password",
    ),
]
