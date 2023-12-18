from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _

from clinic.dictionaries.models import (
    Ingredient,
    Medicine,
    MedicineForm,
    MedicineType,
    OfficeType,
    Specialization,
)


class ActiveIngredientAdminFilter(SimpleListFilter):
    title = "active ingredient"  # Human-readable title which will be displayed in the right admin sidebar just above the filter options.
    parameter_name = "active_ingredient"  # The name of the query parameter used in the URL for this filter.

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each tuple is the coded value for the option that will appear in the URL query.
        The second element is the human-readable name for the option that will appear in the right sidebar.
        """
        ingredients = Ingredient.objects.filter(
            medicineingredient__isnull=False
        ).distinct()
        return tuple(
            (ingredient.id, ingredient.name) for ingredient in ingredients
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value provided in the query string and retrievable via `self.value()`.
        """
        if self.value():
            return queryset.filter(active_ingredients__id=self.value())


class MedicineFormAdminFilter(SimpleListFilter):
    title = _("form")  # Display title in the admin sidebar.
    parameter_name = "form"  # URL query parameter name.

    def lookups(self, request, model_admin):
        """
        Returns a tuple of tuples. Each inner tuple contains the form ID and its human-readable name.
        """
        forms = MedicineForm.objects.all()
        return tuple((form.id, form.name) for form in forms)

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the selected form value.
        """
        if self.value():
            return queryset.filter(form__id=self.value())
        return queryset


class MedicineTypeAdminFilter(SimpleListFilter):
    title = _("type of medicine")  # Display title in the admin sidebar.
    parameter_name = "type_of_medicine"  # URL query parameter name.

    def lookups(self, request, model_admin):
        """
        Returns a tuple of tuples. Each inner tuple contains the type ID and its human-readable name.
        """
        types = MedicineType.objects.all()
        return tuple((type_.id, type_.name) for type_ in types)

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the selected type value.
        """
        if self.value():
            return queryset.filter(type_of_medicine__id=self.value())
        return queryset


class MedicineAdminFilter(SimpleListFilter):
    title = _(
        "medicine"
    )  # Human-readable title which will be displayed in the right admin sidebar just above the filter options.
    parameter_name = "medicine"  # The name of the query parameter used in the URL for this filter.

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each tuple is the coded value for the option that will appear in the URL query.
        The second element is the human-readable name for the option that will appear in the right sidebar.
        """
        medicines = Medicine.objects.filter(
            prescriptions__isnull=False
        ).distinct()
        return tuple((medicine.id, medicine.name) for medicine in medicines)

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value provided in the query string and retrievable via `self.value()`.
        """
        if self.value():
            return queryset.filter(medicines__id=self.value())


class OfficeTypeAdminFilter(SimpleListFilter):
    title = _("office type")  # Display title in the admin sidebar.
    parameter_name = "office_type"  # URL query parameter name.

    def lookups(self, request, model_admin):
        """
        Returns a tuple of tuples. Each inner tuple contains the office type ID and its human-readable name.
        """
        types = OfficeType.objects.all()
        return tuple((type_.id, type_.name) for type_ in types)

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the selected office type value.
        """
        if self.value():
            return queryset.filter(office_type__id=self.value())
        return queryset


class SpecializationAdminFilter(SimpleListFilter):
    title = _(
        "specialization"
    )  # Human-readable title which will be displayed in the right admin sidebar just above the filter options.
    parameter_name = "specialization"  # The name of the query parameter used in the URL for this filter.

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each tuple is the coded value for the option that will appear in the URL query.
        The second element is the human-readable name for the option that will appear in the right sidebar.
        """
        specializations = Specialization.objects.all()
        return tuple((spec.id, spec.name) for spec in specializations)

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value provided in the query string and retrievable via `self.value()`.
        """
        if self.value():
            return queryset.filter(specializations__id=self.value())
