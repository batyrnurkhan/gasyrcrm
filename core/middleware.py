# core/middleware.py

from django.shortcuts import render

class Handle404Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Check if the status code is 404
        if response.status_code == 404:
            # Render custom 404 page
            return render(request, 'core/404.html', status=404)
        return response
