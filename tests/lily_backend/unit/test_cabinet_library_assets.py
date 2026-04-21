from django.contrib.staticfiles import finders
from django.template.loader import get_template


def test_chart_and_donut_widgets_come_from_codex_django():
    chart_origin = get_template("cabinet/widgets/chart.html").origin.name
    donut_origin = get_template("cabinet/widgets/donut.html").origin.name

    assert "codex_django" in chart_origin
    assert "codex_django" in chart_origin
    assert "codex_django" in donut_origin
    assert "codex_django" in donut_origin


def test_cabinet_runtime_and_alpine_come_from_codex_django():
    cabinet_js = finders.find("cabinet/js/app/cabinet.js")
    alpine_js = finders.find("cabinet/js/vendor/alpine.min.js")

    assert cabinet_js is not None
    assert "codex_django" in cabinet_js
    assert "codex_django" in cabinet_js
    assert alpine_js is not None
    assert "codex_django" in alpine_js
    assert "codex_django" in alpine_js
