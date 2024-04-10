from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
import logging

logger = logging.getLogger(__name__)
class CustomUserAuthenticationBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        CustomUser = get_user_model()
        try:
            user = CustomUser.objects.get(phone_number=username)
            if user.check_password(password):
                return user
            else:
                logger.info("Password check failed for user: %s", username)
        except CustomUser.DoesNotExist:
            logger.info("User does not exist: %s", username)
            return None