from django.contrib import admin
from django.db.models import CharField, Q, Value
from django.db.models.functions import Coalesce, Concat
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from clinic.filters import MedicineAdminFilter
from clinic.treatment.models import Dosage, Prescription, Visit


class VisitAdminConfig(admin.ModelAdmin):
    model = Visit
    search_fields = ("doctor__job_execution_number", "patient__pesel")
    list_filter = (
        "visit_status",
        "date",
        "disease",
        "office",
        "is_remote",
    )
    ordering = ("readable_id",)
    list_display = (
        "readable_id",
        "patient",
        "doctor",
        "date",
        "predicted_end_date",
        "visit_status",
        "office",
        "is_remote",
        "disease",
        "created_at",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "patient",
                    "doctor",
                    "date",
                    "duration_in_minutes",
                    "disease",
                    "office",
                    "is_remote",
                    "notes",
                )
            },
        ),
    )

    def get_queryset(self, request):
        """
        Override the get_queryset method to annotate the queryset with the full names of the doctor and patient.

        This method enhances the base queryset by adding annotations for the full names of the doctor and patient, which are constructed by concatenating the first and last names. These annotations are used to improve the display of Visit instances in the admin interface.
        """
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            # Concatenate the first and last names of the doctor for a full name display.
            full_name_doctor=Concat(
                "doctor__user__first_name",
                Value(" "),
                "doctor__user__last_name",
                output_field=CharField(),
            ),
            # Similarly, concatenate the first and last names of the patient.
            full_name_patient=Concat(
                "patient__user__first_name",
                Value(" "),
                "patient__user__last_name",
                output_field=CharField(),
            ),
        )
        return queryset

    def get_search_results(self, request, queryset, search_term):
        """
        Override the get_search_results method to enable searching by the full names of doctors and patients.

        This method extends the base search functionality, allowing users to search for visits using the concatenated full names of doctors and patients. It provides a more user-friendly search experience in the admin interface.
        """
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )
        if search_term:
            # Extend the search to include full names of doctors and patients.
            queryset |= self.model.objects.annotate(
                full_name_doctor=Concat(
                    "doctor__user__first_name",
                    Value(" "),
                    "doctor__user__last_name",
                    output_field=CharField(),
                ),
                full_name_patient=Concat(
                    "patient__user__first_name",
                    Value(" "),
                    "patient__user__last_name",
                    output_field=CharField(),
                ),
            ).filter(
                Q(full_name_doctor__icontains=search_term)
                | Q(full_name_patient__icontains=search_term)
            )
        return queryset, use_distinct


class DosageInline(admin.TabularInline):
    model = Dosage
    verbose_name = _("medicine")
    extra = 1


class PrescriptionAdminConfig(admin.ModelAdmin):
    model = Prescription
    inlines = (DosageInline,)
    search_fields = (
        "doctor_job_execution_number",
        "patient_pesel",
    )
    list_filter = ("issue_date", MedicineAdminFilter)
    ordering = ("readable_id",)
    list_display = (
        "readable_id",
        "get_patient",
        "get_doctor",
        "issue_date",
        "expiry_date",
        "get_medicines",
        "get_visit",
    )
    fieldsets = (
        (
            _("Prescription information"),
            {
                "fields": (
                    "patient",
                    "doctor",
                    "prescription_code",
                    "description",
                    "visit",
                )
            },
        ),
    )

    def get_patient(self, obj):
        if obj.visit:
            return obj.visit.patient
        return obj.patient

    get_patient.short_description = _("Patient")
    get_patient.admin_order_field = "patient_pesel"

    def get_doctor(self, obj):
        if obj.visit:
            return obj.visit.doctor
        return obj.doctor

    get_doctor.short_description = _("Doctor")
    get_doctor.admin_order_field = "doctor_job_execution_number"

    def get_visit(self, obj):
        if obj.visit:
            url = reverse(
                "admin:%s_%s_change"
                % (obj.visit._meta.app_label, obj.visit._meta.model_name),
                args=[obj.visit.pk],
            )
            return format_html('<a href="{}">{}</a>', url, obj.visit)
        return "---"

    get_visit.short_description = _("Visit")

    def get_medicines(self, obj):
        """Concatenate all medicines with dosages into a comma-separated string."""
        return ", ".join(
            f"{dosage.medicine.name} - {dosage.amount} {dosage.frequency}"
            for dosage in Dosage.objects.filter(prescription=obj)
        )

    get_medicines.short_description = _("Medicines")

    def get_queryset(self, request):
        """
        Override the get_queryset method to annotate the queryset with additional fields.

        This method enhances the base queryset by adding annotations for full names of the doctor and patient, as well as the doctor's job execution number and patient's PESEL. These annotations are used to improve the display and sorting of Prescription instances in the admin interface.
        """
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            # Annotate with the full name of the doctor. It coalesces visit doctor and regular doctor's name to handle cases where visit information might be missing.
            full_name_doctor=Concat(
                Coalesce(
                    "doctor__user__first_name",
                    "visit__doctor__user__first_name",
                    Value(""),
                ),
                Value(" "),
                Coalesce(
                    "doctor__user__last_name",
                    "visit__doctor__user__last_name",
                    Value(""),
                ),
                output_field=CharField(),
            ),
            # Annotate with the doctor's job execution number, coalescing visit and regular doctor's number.
            doctor_job_execution_number=Coalesce(
                "doctor__job_execution_number",
                "visit__doctor__job_execution_number",
            ),
            # Similar annotation for the patient's full name.
            full_name_patient=Concat(
                Coalesce(
                    "patient__user__first_name",
                    "visit__patient__user__first_name",
                    Value(""),
                ),
                Value(" "),
                Coalesce(
                    "patient__user__last_name",
                    "visit__patient__user__last_name",
                    Value(""),
                ),
                output_field=CharField(),
            ),
            # Coalesce patient's PESEL number.
            patient_pesel=Coalesce("patient__pesel", "visit__patient__pesel"),
        )
        return queryset

    def get_search_results(self, request, queryset, search_term):
        """
        Override the get_search_results method to enable searching by doctor's job execution number and patient's PESEL in addition to their names.

        This method allows for more flexible search capabilities in the admin interface, enabling users to search for prescriptions not only by the names of doctors and patients but also by their unique identifiers.
        """
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )
        if search_term:
            # Extend the search to include doctor's job execution number and patient's PESEL.
            queryset |= self.model.objects.annotate(
                doctor_job_execution_number=Coalesce(
                    "doctor__job_execution_number",
                    "visit__doctor__job_execution_number",
                ),
                full_name_doctor=Concat(
                    Coalesce(
                        "doctor__user__first_name",
                        "visit__doctor__user__first_name",
                        Value(""),
                    ),
                    Value(" "),
                    Coalesce(
                        "doctor__user__last_name",
                        "visit__doctor__user__last_name",
                        Value(""),
                    ),
                    output_field=CharField(),
                ),
                patient_pesel=Coalesce(
                    "patient__pesel", "visit__patient__pesel"
                ),
                full_name_patient=Concat(
                    Coalesce(
                        "patient__user__first_name",
                        "visit__patient__user__first_name",
                        Value(""),
                    ),
                    Value(" "),
                    Coalesce(
                        "patient__user__last_name",
                        "visit__patient__user__last_name",
                        Value(""),
                    ),
                    output_field=CharField(),
                ),
            ).filter(
                Q(full_name_doctor__icontains=search_term)
                | Q(doctor_job_execution_number__icontains=search_term)
                | Q(full_name_patient__icontains=search_term)
                | Q(patient_pesel__icontains=search_term)
            )
        return queryset, use_distinct
