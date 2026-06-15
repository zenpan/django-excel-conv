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
from pathlib import Path
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from excel_conv.models import ConvJob
from excel_conv.forms import UploadJobForm
from excel_conv.lib.sources import convert_job, detect_source, SOURCE_CHOICES


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
            'source_choices': SOURCE_CHOICES,
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
        response = super().form_valid(form)
        # Auto-detect and tag the source format (LexisNexis vs NY Supreme Court).
        try:
            self.object.source_type = detect_source(self.object.excel_file.path) or ''
            self.object.save(update_fields=['source_type'])
        except Exception:
            pass
        messages.success(self.request, 'File uploaded successfully!')
        messages.info(self.request, 'Press the "Convert" button on the Jobs page to convert it.')
        return response
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
        succeeded = convert_job(object)
    except Exception:
        object.success = False
        object.save()
        succeeded = False

    if succeeded:
        messages.success(request, 'File converted successfully.')
    else:
        messages.error(
            request,
            object.error or 'Conversion failed. Check that the file is in the expected format.',
        )
    return redirect('jobs')


# --------------------------------------------------
@login_required
def download(request, job_id, which):
    """ Serve a job's source or converted file to logged-in users only.

    The uploaded/converted spreadsheets contain debtor PII, so they are
    streamed through this login-protected view rather than from a public
    /media/ URL.
    """
    job = get_object_or_404(ConvJob, pk=job_id)
    field = {'source': job.excel_file, 'converted': job.conv_file}.get(which)
    if field is None or not field.name or not os.path.exists(field.path):
        raise Http404('File not available.')
    return FileResponse(
        field.open('rb'),
        as_attachment=True,
        filename=os.path.basename(field.name),
    )


# --------------------------------------------------
@login_required
@require_POST
def set_source(request, job_id):
    """ Manually override the detected source format for a job. """
    job = get_object_or_404(ConvJob, pk=job_id)
    choice = request.POST.get('source_type', '').strip()
    valid = {key for key, _ in SOURCE_CHOICES}
    job.source_type = choice if choice in valid else ''
    job.save(update_fields=['source_type'])
    messages.success(request, 'Source format updated.')
    return redirect('jobs')
