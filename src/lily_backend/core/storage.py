from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


def _without_source_mapping_url_patterns(patterns):
    """Keep manifest hashing, but don't require optional sourcemap files."""
    filtered_patterns = []

    for extension, converters in patterns:
        filtered_patterns.append(
            (
                extension,
                tuple(converter for converter in converters if "sourceMappingURL" not in converter[0]),
            )
        )

    return tuple(filtered_patterns)


class ProductionManifestStaticFilesStorage(ManifestStaticFilesStorage):
    patterns = _without_source_mapping_url_patterns(ManifestStaticFilesStorage.patterns)

    missing_vendor_asset_fallbacks = {
        "showcase/cabinet/css/vendor/fonts/bootstrap-icons.woff": "showcase/cabinet/css/fonts/bootstrap-icons.woff",
        "showcase/cabinet/css/vendor/fonts/bootstrap-icons.woff2": "showcase/cabinet/css/fonts/bootstrap-icons.woff2",
    }

    def hashed_name(self, name, content=None, filename=None):
        return super().hashed_name(self.missing_vendor_asset_fallbacks.get(name, name), content, filename)
