import os

import pytest
from django.conf import settings
from django.template import TemplateSyntaxError
from django.template.loader import get_template


def get_all_templates():
    """
    Collects all .html files from the main templates directory.
    """
    template_dir = os.path.join(settings.BASE_DIR, "templates")
    template_files = []

    for root, _dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith(".html"):
                # Get relative path from template_dir
                rel_path = os.path.relpath(os.path.join(root, file), template_dir)
                # Normalize path for Django (use forward slashes)
                rel_path = rel_path.replace(os.sep, "/")
                template_files.append(rel_path)

    return template_files


@pytest.mark.unit
@pytest.mark.parametrize("template_name", get_all_templates())
def test_template_syntax(template_name):
    """
    Attempts to load each template to check for syntax errors.
    """
    try:
        get_template(template_name)
    except TemplateSyntaxError as e:
        pytest.fail(f"Syntax error in template '{template_name}': {e}")
    except Exception as e:
        # Other errors (like missing base templates) might occur,
        # but here we primarily care about syntax.
        # We'll fail on them too as they indicate broken templates.
        pytest.fail(f"Error loading template '{template_name}': {e}")
