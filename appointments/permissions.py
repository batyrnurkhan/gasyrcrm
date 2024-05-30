# appointments/api/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsPsychologistOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'Psychologist'

class IsPsychologist(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Psychologist'

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Student'
