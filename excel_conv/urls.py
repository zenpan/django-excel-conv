from excel_conv import views
from django.urls import path

urlpatterns = [
    path('', views.index, name='index'),
    path('help', views.help_view, name='help'),
    path('jobs', views.jobs, name='jobs'),
    path('upload', views.Upload.as_view(), name='upload'),
    path('convert/<job_id>', views.convert, name='convert'),
    path('delete/<job_id>', views.delete, name='delete'),
]

