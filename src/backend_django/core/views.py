from django.utils import translation
from django.views.generic import TemplateView


class LLMSTextView(TemplateView):
    content_type = "text/plain"

    def get_template_names(self):
        current_language = translation.get_language()
        return [f"llms_{current_language}.txt"]

    def render_to_response(self, context, **response_kwargs):
        # Ensure the template exists for the current language
        try:
            return super().render_to_response(context, **response_kwargs)
        except Exception:
            # Fallback to default language (e.g., German) if specific language template not found
            return TemplateView.as_view(template_name="llms_de.txt", content_type="text/plain")(self.request)
