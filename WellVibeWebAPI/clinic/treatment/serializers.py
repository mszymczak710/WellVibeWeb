from datetime import datetime, timedelta, timezone

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from clinic.dictionaries.serializers import (
    DiseaseSerializer,
    MedicineFormSerializer,
    MedicineNoFormSerializer,
    OfficeSerializer,
)
from clinic.roles.serializers import DoctorReadSerializer, PatientSerializer
from clinic.treatment.choices import VisitStatus
from clinic.treatment.models import Dosage, Prescription, Visit


class VisitReadSerializer(serializers.ModelSerializer):
    doctor = DoctorReadSerializer(read_only=True)
    patient = PatientSerializer(read_only=True)
    disease = DiseaseSerializer(read_only=True)
    office = OfficeSerializer(read_only=True)

    class Meta:
        model = Visit
        fields = "__all__"


class VisitWriteSerializer(serializers.ModelSerializer):
    def validate_date(self, value):
        current_time = datetime.now(timezone.utc)
        if value < current_time:
            raise serializers.ValidationError(_("Date must be in the future."))
        return value

    def validate_duration_in_minutes(self, value):
        if not (10 <= value <= 180):
            raise serializers.ValidationError(
                _("Duration of the visit must be between 10 and 180 minutes.")
            )
        return value

    def validate(self, data):
        # Validation to check if the visit is being modified after starting or completion
        if self.instance and self.instance.visit_status in [
            VisitStatus.IN_PROGRESS,
            VisitStatus.COMPLETED,
        ]:
            raise serializers.ValidationError(
                _("Cannot modify a visit that is in progress or completed.")
            )

        # Validation to prevent changes to the visit within 24 hours of its scheduled start
        if self.instance:
            current_time = datetime.now(timezone.utc)
            time_before_appointment = timedelta(hours=24)
            if self.instance.date - current_time <= time_before_appointment:
                raise serializers.ValidationError(
                    _(
                        "Cannot modify the visit within 24 hours of its scheduled start."
                    )
                )

        # Validation for overlapping visits
        start_time = data.get("date")
        if not start_time:
            raise serializers.ValidationError(_("Invalid start date format."))

        end_time = start_time + timedelta(
            minutes=data.get("duration_in_minutes")
        )
        overlapping_visits = Visit.objects.filter(
            date__lt=end_time, predicted_end_date__gt=start_time
        ).exclude(pk=self.instance.pk if self.instance else None)

        # Check for overlapping visits for the doctor, office, and patient
        if overlapping_visits.filter(doctor=data.get("doctor")).exists():
            raise serializers.ValidationError(
                _("Doctor has an overlapping visit.")
            )

        if overlapping_visits.filter(office=data.get("office")).exists():
            raise serializers.ValidationError(
                _("Office is not available during the selected time.")
            )

        if overlapping_visits.filter(patient=data.get("patient")).exists():
            raise serializers.ValidationError(
                _("Patient has an overlapping visit.")
            )

        return super().validate(data)

    def to_representation(self, instance):
        serializer = VisitReadSerializer(instance)
        return serializer.data

    class Meta:
        model = Visit
        fields = "__all__"
        read_only_fields = (
            "id",
            "readable_id",
            "predicted_end_date",
            "created_at",
            "visit_status",
        )


class DosageReadSerializer(serializers.ModelSerializer):
    medicine = MedicineNoFormSerializer()

    class Meta:
        model = Dosage
        fields = ("medicine", "amount", "frequency")

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Assuming the `Medicine` model's instance has a `form` attribute
        # and MedicineFormSerializer is set up to serialize this form.
        form_representation = MedicineFormSerializer(
            instance.medicine.form
        ).data
        representation["form"] = form_representation
        return representation


class DosageWriteSerializer(serializers.ModelSerializer):
    def validate_amount(self, value):
        if value <= 0 or value > 100:
            raise serializers.ValidationError(
                _("Invalid amount. Must be positive and not exceed 100.")
            )
        return value

    class Meta:
        model = Dosage
        fields = ("medicine", "amount", "frequency")


class PrescriptionReadSerializer(serializers.ModelSerializer):
    doctor = DoctorReadSerializer(read_only=True)
    patient = PatientSerializer(read_only=True)
    dosages = DosageReadSerializer(source="dosage_set", many=True)

    class Meta:
        model = Prescription
        fields = (
            "id",
            "patient",
            "doctor",
            "dosages",
            "readable_id",
            "prescription_code",
            "issue_date",
            "expiry_date",
            "description",
            "visit",
        )


class PrescriptionWriteSerializer(serializers.ModelSerializer):
    dosages = DosageWriteSerializer(many=True, source="dosage_set")

    def validate(self, data):
        visit = data.get("visit")
        patient = data.get("patient")
        doctor = data.get("doctor")

        # If visit is provided
        if visit:
            if patient or doctor:
                raise serializers.ValidationError(
                    _(
                        "Cannot provide patient or doctor when visit is provided."
                    )
                )

            # Set patient and doctor from visit
            data["patient"] = visit.patient
            data["doctor"] = visit.doctor

        # If visit is not provided, both patient and doctor must be
        elif not patient or not doctor:
            raise serializers.ValidationError(
                _(
                    "Either the visit must be provided, or both patient and doctor must be provided."
                )
            )

        return data

    def create(self, validated_data):
        dosages_data = validated_data.pop("dosage_set")
        prescription = Prescription.objects.create(**validated_data)
        for dosage_data in dosages_data:
            Dosage.objects.create(prescription=prescription, **dosage_data)

        return prescription

    def to_representation(self, instance):
        serializer = PrescriptionReadSerializer(instance)
        return serializer.data

    class Meta:
        model = Prescription
        fields = "__all__"
        read_only_fields = ("id", "readable_id", "issue_date", "expiry_date")
