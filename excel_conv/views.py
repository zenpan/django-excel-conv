""" This module contains the views for the excel_conv app
    
        The views are:
            index
            help_view
            about
            jobs
            upload
            convert
"""

import os
from django.shortcuts import render, redirect
# from django.http import HttpResponse
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from excel_conv.models import ConvJob
from excel_conv.forms import UploadJobForm
from excel_conv.lib.convert import convert_sheet


# --------------------------------------------------
def index(request):
    """ The index view for the program """
    print(request)
    context = { 'welcome_text': 'Doyaga Law Firm Apps'}
    return render(request, 'index.html', context)


# --------------------------------------------------
def delete(request, job_id):
    """ The delete view for the program """
    object = ConvJob.objects.get(pk=job_id)
    object.delete()
    os.remove(object.excel_file.path)
    if object.conv_file:
        os.remove(object.conv_file.path)
    return redirect('jobs')


# --------------------------------------------------
def contact(request):
    """ The help view for the program """
    context = {
        'welcome_text': 'Contact'
    }
    return render(request, 'contact.html', context)


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
        'welcome_text': 'Fix Excel MailMerge'
    }
    return render(request, 'about.html', context)


# --------------------------------------------------
@login_required
def jobs(request):
    """ The jobs view for the program """
    all_jobs = ConvJob.objects.all().order_by('-upload_at')
    pagignator = Paginator(all_jobs, 5)
    page_number = request.GET.get('page')
    all_jobs = pagignator.get_page(page_number)
    context = "Conversion Jobs"
    return render(
        request, 'jobs.html',
        {
            'all_jobs': all_jobs, 
            'welcome_text': context,
        }
    )


# --------------------------------------------------
class Upload(LoginRequiredMixin, CreateView):
    """ The upload view for the program """
    model = ConvJob
    form_class = UploadJobForm
    template_name = 'upload.html'
    # if successful add a success message
    def form_valid(self, form):
        messages.success(self.request, 'File uploaded successfully!')
        messages.info(self.request, 'It will take about 30 seconds to convert the file after pressing the "Convert" button.')
        return super().form_valid(form)
    success_url = reverse_lazy('jobs')


# --------------------------------------------------
def convert(request, job_id):
    """ The convert view for the program """
    print(request)
    object = ConvJob.objects.get(pk=job_id)
    print("")
    convert_sheet(object)
    return redirect('jobs')
