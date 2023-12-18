from rest_framework import permissions

from clinic.auth.choices import Role


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        # Checks whether the user is authenticated and has an admin role
        return (
            request.user.is_authenticated and request.user.role == Role.ADMIN
        )


class IsNurse(permissions.BasePermission):
    def has_permission(self, request, view):
        # Checks whether the user is authenticated and has a nurse role
        return (
            request.user.is_authenticated and request.user.role == Role.NURSE
        )


class IsDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        # Checks whether the user is authenticated and has a doctor role
        return (
            request.user.is_authenticated and request.user.role == Role.DOCTOR
        )


class IsPatient(permissions.BasePermission):
    def has_permission(self, request, view):
        # Checks whether the user is authenticated and has a patient role
        return (
            request.user.is_authenticated and request.user.role == Role.PATIENT
        )
