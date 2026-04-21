import os
import pytest
from src.workers.core.base_module.template_renderer import TemplateRenderer
from jinja2 import TemplateNotFound

def test_renderer_init_success(tmp_path):
    # Create a dummy templates directory
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    
    renderer = TemplateRenderer(str(templates_dir))
    assert renderer is not None
    assert renderer.env is not None

def test_renderer_init_failure():
    with pytest.raises(FileNotFoundError):
        TemplateRenderer("/non/existent/path/for/sure")

def test_render_success(tmp_path):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    template_file = templates_dir / "hello.html"
    template_file.write_text("Hello {{ name }}!")
    
    renderer = TemplateRenderer(str(templates_dir))
    result = renderer.render("hello.html", {"name": "Lily"})
    assert result == "Hello Lily!"

def test_render_template_not_found(tmp_path):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    
    renderer = TemplateRenderer(str(templates_dir))
    with pytest.raises(TemplateNotFound):
        renderer.render("missing.html", {})
