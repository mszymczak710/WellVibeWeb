from django_filters import rest_framework as filters

from clinic.roles.models import Doctor, Nurse, Patient


class DoctorFilterSet(filters.FilterSet):
    user__first_name = filters.CharFilter(lookup_expr="icontains")
    user__last_name = filters.CharFilter(lookup_expr="icontains")
    user__email = filters.CharFilter(lookup_expr="icontains")
    job_execution_number = filters.CharFilter(lookup_expr="icontains")
    specializations__name = filters.CharFilter(
        method="filter_by_specializations_name"
    )

    readable_id = filters.NumberFilter()

    class Meta:
        model = Doctor
        fields = (
            "user__first_name",
            "user__last_name",
            "user__email",
            "job_execution_number",
            "specializations__name",
            "readable_id",
        )

    def filter_by_specializations_name(self, queryset, name, value):
        """
        Filters doctors based on the names of specializations.
        """
        names = value.split(",")
        return queryset.filter(specializations__name__in=names).distinct()


class NurseFilterSet(filters.FilterSet):
    user__first_name = filters.CharFilter(lookup_expr="icontains")
    user__last_name = filters.CharFilter(lookup_expr="icontains")
    user__email = filters.CharFilter(lookup_expr="icontains")
    nursing_license_number = filters.CharFilter(lookup_expr="icontains")
    readable_id = filters.NumberFilter()

    class Meta:
        model = Nurse
        fields = (
            "user__first_name",
            "user__last_name",
            "user__email",
            "nursing_license_number",
            "readable_id",
        )


class PatientFilterSet(filters.FilterSet):
    user__first_name = filters.CharFilter(lookup_expr="icontains")
    user__last_name = filters.CharFilter(lookup_expr="icontains")
    user__email = filters.CharFilter(lookup_expr="icontains")
    pesel = filters.CharFilter(lookup_expr="icontains")
    readable_id = filters.NumberFilter()

    class Meta:
        model = Patient
        fields = (
            "user__first_name",
            "user__last_name",
            "user__email",
            "pesel",
            "readable_id",
        )
