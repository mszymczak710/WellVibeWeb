import requests

from core import settings


def verify_recaptcha(response):
    """
    Verify the reCAPTCHA response with the reCAPTCHA service.
    """
    # Prepare the data payload for the verification request
    data = {
        "secret": settings.RECAPTCHA_SECRET_KEY,  # The secret key for server-side verification
        "response": response,  # The response token from the reCAPTCHA widget on the client
    }

    # Make a POST request to the reCAPTCHA verification URL with the payload
    response = requests.post(settings.RECAPTCHA_VERIFY_URL, data=data)

    # Parse the JSON response from the reCAPTCHA service
    result = response.json()

    # Return the 'success' value to indicate if the reCAPTCHA challenge was passed
    return result.get("success")
