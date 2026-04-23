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
