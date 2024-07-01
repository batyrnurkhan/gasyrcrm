from rest_framework import permissions

class IsMentorSuperuserOrGroupMember(permissions.BasePermission):
    """
    Custom permission to only allow mentors, superusers, or group members to view or edit a lesson.
    """

    def has_object_permission(self, request, view, obj):
        # Check if the user is a mentor or superuser
        if request.user.role == 'Mentor' or request.user.is_superuser:
            return True

        # Check if the user is part of the group template associated with the lesson
        return obj.students.filter(id=request.user.id).exists()