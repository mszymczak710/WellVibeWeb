from django.contrib import admin
from django.contrib.auth.models import Group

from clinic.auth.admin import UserAdminConfig
from clinic.auth.models import User
from clinic.dictionaries.admin import (
    DiseaseAdminConfig,
    MedicineAdminConfig,
    OfficeAdminConfig,
    SpecializationAdminConfig,
)
from clinic.dictionaries.models import (
    Disease,
    Medicine,
    Office,
    Specialization,
)
from clinic.roles.admin import (
    DoctorAdminConfig,
    NurseAdminConfig,
    PatientAdminConfig,
)
from clinic.roles.models import Doctor, Nurse, Patient
from clinic.treatment.admin import PrescriptionAdminConfig, VisitAdminConfig
from clinic.treatment.models import Prescription, Visit

admin.site.unregister(Group)
admin.site.register(User, UserAdminConfig)
admin.site.register(Doctor, DoctorAdminConfig)
admin.site.register(Nurse, NurseAdminConfig)
admin.site.register(Patient, PatientAdminConfig)
admin.site.register(Disease, DiseaseAdminConfig)
admin.site.register(Medicine, MedicineAdminConfig)
admin.site.register(Office, OfficeAdminConfig)
admin.site.register(Specialization, SpecializationAdminConfig)
admin.site.register(Prescription, PrescriptionAdminConfig)
admin.site.register(Visit, VisitAdminConfig)
