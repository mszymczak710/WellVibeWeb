from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter

from clinic.auth.choices import Role
from clinic.pagination import StandardResultsSetPagination
from clinic.permissions import IsAdmin, IsDoctor, IsNurse, IsPatient
from clinic.throttling import DoctorRateThrottle, NurseRateThrottle
from clinic.treatment.filters import PrescriptionFilter, VisitFilter
from clinic.treatment.models import Prescription, Visit
from clinic.treatment.querysets import (
    get_prescription_queryset,
    get_visit_queryset,
)
from clinic.treatment.serializers import (
    PrescriptionReadSerializer,
    PrescriptionWriteSerializer,
    VisitReadSerializer,
    VisitWriteSerializer,
)


@extend_schema(
    methods=("post", "patch"),
    request=VisitWriteSerializer,
    responses={200: VisitReadSerializer},
)
class VisitViewSet(viewsets.ModelViewSet):
    permission_classes = (IsNurse | IsDoctor | IsAdmin | IsPatient,)
    queryset = Visit.objects.all()
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = VisitFilter
    ordering_fields = (
        "date",
        "visit_status",
        "duration_in_minutes",
        "is_remote",
        "created_at",
        "readable_id",
        "patient__pesel",
        "doctor__job_execution_number",
        "office__name",
        "disease__name",
    )
    pagination_class = StandardResultsSetPagination
    http_method_names = ("get", "post", "delete", "patch", "head", "options")

    def get_permissions(self):
        if self.action in ("create", "destroy", "partial_update"):
            self.permission_classes = (IsNurse | IsAdmin,)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return VisitReadSerializer
        return VisitWriteSerializer

    def get_queryset(self):
        return get_visit_queryset(self.request.user)

    def get_throttles(self):
        if self.action in ("create", "destroy", "partial_update"):
            self.throttle_classes = (NurseRateThrottle,)
        return super().get_throttles()


@extend_schema(
    methods=("post",),
    request=PrescriptionWriteSerializer,
    responses={200: PrescriptionReadSerializer},
)
class PrescriptionViewSet(viewsets.ModelViewSet):
    permission_classes = (IsNurse | IsDoctor | IsAdmin | IsPatient,)
    queryset = Prescription.objects.all()
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = PrescriptionFilter
    ordering_fields = (
        "issue_date",
        "expiry_date",
        "patient__pesel",
        "doctor__job_execution_number",
    )
    pagination_class = StandardResultsSetPagination
    http_method_names = ("get", "post", "delete", "head", "options")

    def get_permissions(self):
        if self.action in ("create", "destroy"):
            self.permission_classes = (IsDoctor | IsAdmin,)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return PrescriptionReadSerializer
        return PrescriptionWriteSerializer

    def get_queryset(self):
        return get_prescription_queryset(self.request.user)

    def get_throttles(self):
        if self.action == "create":
            self.throttle_classes = (DoctorRateThrottle,)
        return super().get_throttles()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if (
            request.user.role == Role.DOCTOR
            and instance.doctor.user != request.user
        ):
            raise PermissionDenied(
                _("You do not have permission to perform this action.")
            )
        return super().destroy(request, *args, **kwargs)
