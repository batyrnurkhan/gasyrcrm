from django.http import HttpResponseForbidden
from django.views.generic import View

class TeacherSuperuserMixin(View):
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.role == 'Teacher'):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


#Не юзал просто создал