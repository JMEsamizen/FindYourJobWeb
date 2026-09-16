import ast
import gettext
from pathlib import Path
from django.conf import settings
from django.utils.translation import trans_real


class PoCatalog(gettext.NullTranslations):
    def __init__(self, entries):
        super().__init__()
        self.entries = entries

    def gettext(self, message):
        return self.entries.get(message, message)

    def ngettext(self, singular, plural, number):
        return self.gettext(singular if number == 1 else plural)


def _read_po(path):
    entries = {}
    current = None
    parts = []
    field = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("msgid ") or line.startswith("msgstr "):
            if field == "msgid" and current is not None and parts:
                current = "".join(parts)
            field = "msgid" if line.startswith("msgid ") else "msgstr"
            parts = [ast.literal_eval(line.split(" ", 1)[1])]
            if field == "msgstr" and current is not None:
                value = "".join(parts)
                if current:
                    entries[current] = value
                parts = []
        elif line.startswith('"') and field:
            parts.append(ast.literal_eval(line))
        elif not line and field == "msgstr" and current is not None:
            value = "".join(parts)
            if current and value:
                entries[current] = value
            current = None
            parts = []
            field = None
        if line.startswith("msgid "):
            current = ast.literal_eval(line.split(" ", 1)[1])
    if current and field == "msgstr":
        value = "".join(parts)
        if value:
            entries[current] = value
    return entries


class PoFallbackMiddleware:
    """Load PO files when msgfmt has not produced MO files in development."""

    def __init__(self, get_response):
        self.get_response = get_response
        for language, _label in settings.LANGUAGES:
            if language == settings.LANGUAGE_CODE:
                continue
            mo_path = Path(settings.BASE_DIR) / "locale" / language / "LC_MESSAGES" / "django.mo"
            po_path = mo_path.with_suffix(".po")
            if not mo_path.exists() and po_path.exists():
                trans_real._translations[language] = PoCatalog(_read_po(po_path))

    def __call__(self, request):
        return self.get_response(request)
