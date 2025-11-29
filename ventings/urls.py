from django.urls import path

from .views import ventings_view

urlpatterns = [
    path('ventings/', ventings_view, name='ventings'),
]

