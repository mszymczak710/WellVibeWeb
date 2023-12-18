from django_filters import rest_framework as filters

from clinic.treatment.choices import VisitStatus
from clinic.treatment.models import Prescription, Visit


class VisitFilter(filters.FilterSet):
    date = filters.DateTimeFromToRangeFilter()
    duration_in_minutes = filters.RangeFilter()
    visit_status = filters.ChoiceFilter(choices=VisitStatus.choices)
    patient__pesel = filters.CharFilter(lookup_expr="icontains")
    doctor__job_execution_number = filters.CharFilter(lookup_expr="icontains")
    office__office_type__name = filters.CharFilter(lookup_expr="icontains")
    office__floor = filters.NumberFilter()
    is_remote = filters.BooleanFilter()
    disease__name = filters.CharFilter(lookup_expr="icontains")
    created_at = filters.DateTimeFromToRangeFilter()
    readable_id = filters.NumberFilter()

    class Meta:
        model = Visit
        fields = (
            "date",
            "duration_in_minutes",
            "visit_status",
            "patient__pesel",
            "doctor__job_execution_number",
            "office__office_type__name",
            "office__floor",
            "is_remote",
            "disease__name",
            "created_at",
            "readable_id",
        )


class PrescriptionFilter(filters.FilterSet):
    issue_date = filters.DateFromToRangeFilter()
    expiry_date = filters.DateFromToRangeFilter()
    medicine = filters.CharFilter(
        field_name="dosage__medicine__name", lookup_expr="icontains"
    )
    patient__pesel = filters.CharFilter(lookup_expr="icontains")
    doctor__job_execution_number = filters.CharFilter(lookup_expr="icontains")
    readable_id = filters.NumberFilter()
    visit = filters.ModelChoiceFilter(
        queryset=Visit.objects.all(),
        field_name="visit",
        to_field_name="id",
    )

    class Meta:
        model = Prescription
        fields = (
            "issue_date",
            "expiry_date",
            "medicine",
            "patient__pesel",
            "doctor__job_execution_number",
            "readable_id",
            "visit",
        )
