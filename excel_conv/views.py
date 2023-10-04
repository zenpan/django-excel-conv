""" This module contains the views for the excel_conv app
    
        The views are:
            index
            help_view
            about
            jobs
            upload
            convert
"""

from django.shortcuts import render, redirect
# from django.http import HttpResponse
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from .models import ConvJob
from .forms import UploadJobForm
from .lib.convert import convert_sheet


# --------------------------------------------------
def index(request):
    """ The index view for the program """
    print(request)
    return redirect('upload')


# --------------------------------------------------
def help_view(request):
    """ The help view for the program """
    context = {
        'welcome_text': 'Help'
    }
    return render(request, 'help.html', context)


# --------------------------------------------------
def about(request):
    """ The about view for the program """
    context = {
        'welcome_text': 'About this program:  Fix Excel MailMerge'
    }
    return render(request, 'about.html', context)


# --------------------------------------------------
def jobs(request):
    """ The jobs view for the program """
    all_jobs = ConvJob.objects.all().order_by('-upload_at')
    context = "Conversion Jobs"
    return render(
        request, 'jobs.html',
        {
            'all_jobs': all_jobs, 
            'welcome_text': context,
        }
    )


# --------------------------------------------------
class Upload(CreateView):
    """ The upload view for the program """
    model = ConvJob
    form_class = UploadJobForm
    template_name = 'upload.html'
    success_url = reverse_lazy('jobs')


# --------------------------------------------------
def convert(request, job_id):
    """ The convert view for the program """
    print(request)
    object = ConvJob.objects.get(pk=job_id)
    print("")
    convert_sheet(object)
    return redirect('jobs')
