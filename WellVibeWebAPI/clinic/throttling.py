from rest_framework.throttling import UserRateThrottle


class DoctorRateThrottle(UserRateThrottle):
    scope = "doctor"  # This should correspond to a DRF_THROTTLE_RATES setting with a 'doctor' key


class NurseRateThrottle(UserRateThrottle):
    scope = "nurse"  # This should correspond to a DRF_THROTTLE_RATES setting with a 'nurse' key


class PatientRateThrottle(UserRateThrottle):
    scope = "patient"  # This should correspond to a DRF_THROTTLE_RATES setting with a 'patient' key
