from core.logger import log
from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.template.exceptions import TemplateDoesNotExist
from django.utils import translation
from django.views import View
from django.views.generic import TemplateView


class RootRedirectView(View):
    """
    Handles 301 Permanent Redirect from / to the default language prefix (e.g., /de/).
    This is crucial for SEO (Google) to index the localized version as the main one.
    """

    def get(self, request, *args, **kwargs):
        # Get the default language from settings (e.g., 'de')
        default_lang = settings.LANGUAGE_CODE.split("-")[0]

        # Construct the URL for the main page in the default language
        # We use 'main:index' or similar if available, or just hardcode /de/
        # Since we are in core, we'll try to resolve the root of the i18n patterns
        target_url = f"/{default_lang}/"

        log.info(f"SEO: 301 Redirect from / to {target_url}")
        return HttpResponsePermanentRedirect(target_url)


class LLMSTextView(TemplateView):
    content_type = "text/plain"

    def get_template_names(self):
        current_language = translation.get_language()
        log.debug(f"View: LLMSTextView | Action: GetTemplate | lang={current_language}")
        return [f"llms_{current_language}.txt"]

    def render_to_response(self, context, **response_kwargs):
        # Ensure the template exists for the current language
        try:
            return super().render_to_response(context, **response_kwargs)
        except TemplateDoesNotExist:
            log.warning(
                f"View: LLMSTextView | Action: Fallback | lang={translation.get_language()} | fallback={settings.LANGUAGE_CODE}"
            )
            # Fallback to default language (e.g., German) if specific language template not found
            return TemplateView.as_view(template_name=f"llms_{settings.LANGUAGE_CODE}.txt", content_type="text/plain")(
                self.request
            )
