from django_filters import rest_framework as filters

from clinic.dictionaries.models import (
    Disease,
    Medicine,
    Office,
    Specialization,
)


class DiseaseFilterSet(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    readable_id = filters.NumberFilter()

    class Meta:
        model = Disease
        fields = ("name", "readable_id")


class MedicineFilterSet(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    type_of_medicine__name = filters.CharFilter(lookup_expr="icontains")
    form__name = filters.CharFilter(lookup_expr="icontains")
    active_ingredients__name = filters.CharFilter(
        method="filter_by_active_ingredient"
    )
    readable_id = filters.NumberFilter()

    class Meta:
        model = Medicine
        fields = (
            "name",
            "type_of_medicine__name",
            "form__name",
            "active_ingredients__name",
            "readable_id",
        )

    def filter_by_active_ingredient(self, queryset, name, value):
        """
        Filters drugs based on the name of the active ingredient.
        """
        ingredient_names = value.split(",")
        return queryset.filter(
            medicineingredient__ingredient__name__in=ingredient_names
        ).distinct()


class OfficeFilterSet(filters.FilterSet):
    office_type__name = filters.CharFilter(lookup_expr="icontains")
    floor = filters.NumberFilter()
    readable_id = filters.NumberFilter()

    class Meta:
        model = Office
        fields = ("office_type__name", "floor", "readable_id")


class SpecializationFilterSet(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    readable_id = filters.NumberFilter()

    class Meta:
        model = Specialization
        fields = ("name", "readable_id")
