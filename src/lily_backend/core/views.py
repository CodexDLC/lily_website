from django.conf import settings
from django.template.exceptions import TemplateDoesNotExist
from django.utils import translation
from django.views.generic import TemplateView


class LLMSTextView(TemplateView):
    content_type = "text/plain"

    def get_template_names(self) -> list[str]:
        current_language = (translation.get_language() or settings.LANGUAGE_CODE).split("-")[0]
        return [f"llms_{current_language}.txt"]

    def render_to_response(self, context, **response_kwargs):
        try:
            return super().render_to_response(context, **response_kwargs)
        except TemplateDoesNotExist:
            fallback_language = settings.LANGUAGE_CODE.split("-")[0]
            return TemplateView.as_view(
                template_name=f"llms_{fallback_language}.txt",
                content_type=self.content_type,
            )(self.request)
