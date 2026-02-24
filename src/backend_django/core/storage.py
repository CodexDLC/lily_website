from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class SelectiveManifestStorage(ManifestStaticFilesStorage):
    """ManifestStaticFilesStorage that skips url() post-processing for source
    CSS partials in css/base/. These files are compiled into app.css and are
    not served directly, so their url() paths don't need to be hashed."""

    _SKIP_DIRS = ("css/base/",)

    def url_converter(self, name, hashed_files, template=None):
        if any(name.startswith(d) for d in self._SKIP_DIRS):
            return lambda url: url
        return super().url_converter(name, hashed_files, template)
