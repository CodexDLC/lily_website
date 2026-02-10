from django.db import models
from django.utils.translation import gettext_lazy as _
from features.system.models.mixins import ActiveMixin, SeoMixin, TimestampMixin


class Category(TimestampMixin, ActiveMixin, SeoMixin):
    """
    Service Category (e.g. Manicure, Pedicure, Haircut).
    These are detailed categories. On the main page, they are grouped by 'bento_group'.
    """

    BENTO_GROUPS = [
        ("hair", _("Friseur & Styling")),
        ("nails", _("Nagelservice")),
        ("face", _("Kosmetologie")),
        ("eyes", _("Brows & Lashes")),
        ("body", _("Massage & Relax")),
        ("hair_removal", _("Depilation")),
    ]

    title = models.CharField(max_length=255, verbose_name=_("Title"), help_text=_("Category name (e.g. 'Maniküre')."))
    slug = models.SlugField(unique=True, verbose_name=_("Slug"), help_text=_("URL part (e.g. 'manicure')."))
    bento_group = models.CharField(
        max_length=20,
        choices=BENTO_GROUPS,
        default="hair",
        verbose_name=_("Bento Group"),
        help_text=_("Group for the main page grid (e.g. 'Nails' combines Manicure & Pedicure)."),
    )
    image = models.ImageField(
        upload_to="categories/",
        verbose_name=_("Image"),
        help_text=_("Background image for Hero section and Bento card."),
    )
    description = models.TextField(
        blank=True, verbose_name=_("Short Description"), help_text=_("Short description displayed in the Hero section.")
    )
    content = models.TextField(
        blank=True,
        verbose_name=_("SEO Text / Content"),
        help_text=_("Detailed text displayed at the bottom of the category page."),
    )
    icon = models.FileField(
        upload_to="categories/icons/",
        blank=True,
        null=True,
        verbose_name=_("Icon"),
        help_text=_("SVG icon for menu or footer (optional)."),
    )
    order = models.PositiveIntegerField(
        default=0, verbose_name=_("Order"), help_text=_("Sorting order (lower numbers come first).")
    )

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["order", "title"]

    def __str__(self):
        return f"{self.title} ({self.get_bento_group_display()})"
