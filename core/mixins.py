from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied

class RoleRequiredMixin(AccessMixin):
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if hasattr(request.user, 'role') and request.user.role in self.allowed_roles:
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied

