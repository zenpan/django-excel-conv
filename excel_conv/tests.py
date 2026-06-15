import shutil
import tempfile
from io import BytesIO
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from openpyxl import Workbook, load_workbook

from excel_conv.lib.convert import convert_sheet
from excel_conv.models import ConvJob


TEST_MEDIA_ROOT = Path(tempfile.mkdtemp(prefix="excel-conv-test-media-"))


def make_source_workbook():
    workbook = Workbook()
    worksheet = workbook.active
    worksheet["A1"] = "No."
    worksheet["B3"] = "DOE, JOHN Q"
    worksheet["C3"] = "123 Main St\nNewark, NJ 07102\nEssex County"
    worksheet["E3"] = "Creditor LLC"
    worksheet["A6"] = "Permissible Use:"

    stream = BytesIO()
    workbook.save(stream)
    workbook.close()
    stream.seek(0)
    return stream.getvalue()


def make_multi_sheet_source_workbook():
    """A workbook whose data is NOT on the active sheet, mirroring the Florida
    exports: an empty 'Sheet1' is active and the records live on the
    'Public Records Results List' sheet."""
    workbook = Workbook()
    workbook.active.title = "Sheet1"  # empty stub, active by default
    data = workbook.create_sheet("Public Records Results List")
    data["A1"] = "No."
    data["B3"] = "DOE, JANE Q"
    data["C3"] = "123 Main St\nMiami, FL 33101-1234\nMiami-Dade County"
    data["E3"] = "Creditor LLC"
    data["A6"] = "Permissible Use:"

    stream = BytesIO()
    workbook.save(stream)
    workbook.close()
    stream.seek(0)
    return stream.getvalue()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ConversionTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        (TEST_MEDIA_ROOT / "excel_files").mkdir(parents=True, exist_ok=True)
        (TEST_MEDIA_ROOT / "conv_files").mkdir(parents=True, exist_ok=True)

    def test_convert_sheet_creates_mail_merge_workbook(self):
        job = ConvJob.objects.create(
            excel_file=SimpleUploadedFile(
                "source.xlsx",
                make_source_workbook(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        )

        self.assertTrue(convert_sheet(job))

        job.refresh_from_db()
        self.assertTrue(job.success)
        self.assertIsNotNone(job.conv_at)

        converted = load_workbook(TEST_MEDIA_ROOT / job.conv_file.name)
        worksheet = converted.active
        self.assertEqual(
            [worksheet[f"{column}1"].value for column in "ABCDEF"],
            ["name", "ADDRESS_1", "City", "State", "Zip", "Creditor"],
        )
        self.assertEqual(
            [worksheet[f"{column}2"].value for column in "ABCDEF"],
            ["JOHN Q DOE", "123 Main St", "Newark", "NJ", "07102", "Creditor LLC"],
        )
        converted.close()

    def test_convert_finds_data_sheet_when_not_active(self):
        # Regression for the Florida exports (the production /convert/517
        # incident): records live on the 'Public Records Results List' sheet
        # while an empty 'Sheet1' is active. The converter must find the data
        # sheet rather than blindly reading workbook.active.
        job = ConvJob.objects.create(
            excel_file=SimpleUploadedFile(
                "FL_SOUTH.xlsx", make_multi_sheet_source_workbook()
            )
        )

        self.assertTrue(convert_sheet(job))

        job.refresh_from_db()
        self.assertTrue(job.success)
        converted = load_workbook(TEST_MEDIA_ROOT / job.conv_file.name)
        worksheet = converted.active
        self.assertEqual(
            [worksheet[f"{column}2"].value for column in "ABCDEF"],
            ["JANE Q DOE", "123 Main St", "Miami", "FL", "33101-1234", "Creditor LLC"],
        )
        converted.close()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ViewTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        (TEST_MEDIA_ROOT / "excel_files").mkdir(parents=True, exist_ok=True)
        (TEST_MEDIA_ROOT / "conv_files").mkdir(parents=True, exist_ok=True)
        self.user = User.objects.create_user(username="tester", password="password")

    def test_public_pages_render(self):
        for url_name in ("index", "about", "contact", "help"):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)

    def test_job_pages_require_login(self):
        for url_name, args in (
            ("jobs", None),
            ("upload", None),
            ("convert", [1]),
            ("delete", [1]),
        ):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name, args=args))
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response["Location"])

    def test_authenticated_upload_creates_job(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("upload"),
            {
                "excel_file": SimpleUploadedFile(
                    "source.xlsx",
                    make_source_workbook(),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

        self.assertRedirects(response, reverse("jobs"))
        self.assertEqual(ConvJob.objects.count(), 1)

    def test_jobs_page_renders_success_state(self):
        self.client.force_login(self.user)
        ConvJob.objects.create(
            excel_file=SimpleUploadedFile("source.xlsx", make_source_workbook()),
            conv_file="conv_files/source_converted.xlsx",
            success=True,
        )

        response = self.client.get(reverse("jobs"))

        self.assertContains(response, "Completed")
        self.assertContains(response, "Done")

    def test_convert_missing_job_returns_404_not_500(self):
        # Regression: /convert/<missing id> used to raise DoesNotExist -> HTTP 500.
        # It must be 404.
        self.client.force_login(self.user)
        response = self.client.get(reverse("convert", args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_delete_missing_job_returns_404_not_500(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("delete", args=[517]))
        self.assertEqual(response.status_code, 404)

    def test_convert_existing_job_succeeds(self):
        self.client.force_login(self.user)
        job = ConvJob.objects.create(
            excel_file=SimpleUploadedFile("source.xlsx", make_source_workbook()),
        )

        response = self.client.get(reverse("convert", args=[job.id]))

        self.assertRedirects(response, reverse("jobs"))
        job.refresh_from_db()
        self.assertTrue(job.success)

    def test_convert_unparseable_file_fails_gracefully(self):
        # Regression for the production /convert/517 incident: an Excel file
        # without the expected "No." / "Permissible Use:" markers (e.g. the
        # Florida export) raised UnboundLocalError -> HTTP 500. It must now
        # redirect with an error message instead of crashing.
        self.client.force_login(self.user)
        workbook = Workbook()
        workbook.active["A1"] = "completely different layout"
        stream = BytesIO()
        workbook.save(stream)
        workbook.close()
        stream.seek(0)
        job = ConvJob.objects.create(
            excel_file=SimpleUploadedFile("FL_SOUTH.xlsx", stream.getvalue()),
        )

        response = self.client.get(reverse("convert", args=[job.id]))

        self.assertRedirects(response, reverse("jobs"))
        job.refresh_from_db()
        self.assertFalse(job.success)
