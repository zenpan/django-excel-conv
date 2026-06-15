"""Source-format registry: detect a file's source and dispatch to its converter.

Adding a new input format = add a converter module (with ``detect`` and a
``convert`` callable) and one entry here. The Convert action calls
``convert_job``; the upload view and the manual-override use ``detect_source``
and ``SOURCE_CHOICES``.
"""
from excel_conv.lib.convert import convert_sheet, detect_lexisnexis
from excel_conv.lib.nysc import convert_nysc_sheet, detect_nysc

# key -> {label, detect(path)->bool, convert(job)->bool}
SOURCES = {
    "lexisnexis": {
        "label": "LexisNexis",
        "detect": detect_lexisnexis,
        "convert": convert_sheet,
    },
    "nysc": {
        "label": "NY Supreme Court",
        "detect": detect_nysc,
        "convert": convert_nysc_sheet,
    },
}

# Order auto-detection is attempted in.
DETECT_ORDER = ("lexisnexis", "nysc")

# (value, label) pairs for the model field and the override dropdown.
SOURCE_CHOICES = [(key, SOURCES[key]["label"]) for key in DETECT_ORDER]


def detect_source(path):
    """Return the source key for a file, or None if it matches no known format."""
    for key in DETECT_ORDER:
        try:
            if SOURCES[key]["detect"](path):
                return key
        except Exception:
            continue
    return None


def source_label(key):
    """Human-readable label for a source key ('' if unknown/blank)."""
    entry = SOURCES.get(key or "")
    return entry["label"] if entry else ""


def convert_job(object):
    """Convert a job using its stored source type, or auto-detect it.

    Falls back to detection when ``source_type`` is unset, records the detected
    type, and fails gracefully (no exception) when the format is unrecognized.
    """
    key = (object.source_type or "").strip() or detect_source(object.excel_file.path)
    if key not in SOURCES:
        object.success = False
        object.error = (
            "Could not determine the file's source format "
            "(not a recognized LexisNexis or NY Supreme Court export)."
        )
        object.save()
        return False
    if object.source_type != key:
        object.source_type = key
        object.save(update_fields=["source_type"])
    return SOURCES[key]["convert"](object)
