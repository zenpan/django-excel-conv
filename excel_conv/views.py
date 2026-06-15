""" This module contains the views for the excel_conv app
    
        The views are:
            index
            help_view
            about
            jobs
            upload
            convert
"""

from pathlib import Path
from django.shortcuts import render, redirect, get_object_or_404
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
    context = { 'welcome_text': 'Doyaga Law Firm Apps'}
    return render(request, 'index.html', context)


# --------------------------------------------------
@login_required
def delete(request, job_id):
    """ The delete view for the program """
    object = get_object_or_404(ConvJob, pk=job_id)
    excel_file_path = Path(object.excel_file.path)
    conv_file_path = Path(object.conv_file.path) if object.conv_file else None
    object.delete()
    if excel_file_path.exists():
        excel_file_path.unlink()
    if conv_file_path and conv_file_path.exists():
        conv_file_path.unlink()
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
@login_required
def convert(request, job_id):
    """ Run the conversion for a single job and report the outcome.

    Uses get_object_or_404 so a missing job returns 404 (not a 500), and
    guards the conversion so a bad/oversized file can never bubble up as a
    server error -- the user gets a message instead.
    """
    object = get_object_or_404(ConvJob, pk=job_id)
    try:
        convert_sheet(object)
        messages.success(request, 'File converted successfully.')
    except Exception:
        object.success = False
        object.save()
        messages.error(
            request,
            'Conversion failed. Check that the file is in the expected format.',
        )
    return redirect('jobs')
