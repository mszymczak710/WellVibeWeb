from rest_framework import serializers

from clinic.auth.serializers import UserReadSerializer
from clinic.dictionaries.serializers import SpecializationSerializer
from clinic.roles.models import Doctor, Nurse, Patient
from clinic.serializers import AddressSerializer


class DoctorReadSerializer(serializers.ModelSerializer):
    user = UserReadSerializer()
    specializations = SpecializationSerializer(many=True)

    class Meta:
        model = Doctor
        fields = "__all__"


class DoctorWriteSerializer(serializers.ModelSerializer):
    user = UserReadSerializer(read_only=True)

    class Meta:
        model = Doctor
        fields = "__all__"
        read_only_fields = (
            "id",
            "readable_id",
            "job_execution_number",
        )

    def to_representation(self, instance):
        serializer = DoctorReadSerializer(instance)
        return serializer.data


class NurseSerializer(serializers.ModelSerializer):
    user = UserReadSerializer(read_only=True)

    class Meta:
        model = Nurse
        fields = "__all__"


class PatientSerializer(serializers.ModelSerializer):
    user = UserReadSerializer(read_only=True)
    address = AddressSerializer()

    class Meta:
        model = Patient
        fields = (
            "user",
            "address",
            "readable_id",
            "id",
            "pesel",
            "phone_number",
        )
        read_only_fields = (
            "id",
            "readable_id",
            "pesel",
        )

    def update(self, instance, validated_data):
        """
        Updates the Patient instance with the given validated data.

        Overridden to handle the update of the nested Address object associated
        with the Patient. If address data is provided, it updates the Address instance
        after updating the Patient instance with the rest of the validated data.
        Saves both the Patient and Address instances after updating.
        """
        address_data = validated_data.pop("address", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if address_data:
            address = instance.address
            for address_attr, address_value in address_data.items():
                setattr(address, address_attr, address_value)
            address.save()

        return instance
