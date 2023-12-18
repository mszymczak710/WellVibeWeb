from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter

from clinic.dictionaries.filters import (
    DiseaseFilterSet,
    MedicineFilterSet,
    OfficeFilterSet,
    SpecializationFilterSet,
)
from clinic.dictionaries.models import (
    Disease,
    Medicine,
    Office,
    Specialization,
)
from clinic.dictionaries.serializers import (
    DiseaseSerializer,
    MedicineSerializer,
    OfficeSerializer,
    SpecializationSerializer,
)
from clinic.pagination import StandardResultsSetPagination
from clinic.permissions import IsAdmin, IsDoctor, IsNurse, IsPatient


class DiseaseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Disease.objects.all()
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = DiseaseFilterSet
    ordering_fields = ("name", "readable_id")
    serializer_class = DiseaseSerializer
    permission_classes = (IsDoctor | IsAdmin,)
    pagination_class = StandardResultsSetPagination


class MedicineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Medicine.objects.all()
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = MedicineFilterSet
    ordering_fields = (
        "name",
        "type_of_medicine__name",
        "form__name",
        "readable_id",
    )
    serializer_class = MedicineSerializer
    permission_classes = (IsDoctor | IsAdmin,)
    pagination_class = StandardResultsSetPagination


class OfficeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Office.objects.all()
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = OfficeFilterSet
    ordering_fields = ("office_type__name", "floor", "readable_id")
    serializer_class = OfficeSerializer
    permission_classes = (IsDoctor | IsAdmin | IsNurse | IsPatient,)
    pagination_class = StandardResultsSetPagination


class SpecializationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Specialization.objects.all()
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = SpecializationFilterSet
    ordering_fields = ("name", "readable_id")
    serializer_class = SpecializationSerializer
    permission_classes = (IsDoctor | IsAdmin,)
    pagination_class = StandardResultsSetPagination
