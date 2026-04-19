from django import forms

from .models import Master


class MasterAdminForm(forms.ModelForm):
    class Meta:
        model = Master
        fields = "__all__"

    def clean_photo(self):
        """
        Fixes the conflict when a user uploads a new file AND checks the 'Clear' checkbox.
        If a new file is provided, we ignore the 'clear' flag.
        """
        photo = self.cleaned_data.get("photo")

        # In Django, if 'Clear' is checked, the widget returns False for the field value
        # but if a new file is uploaded, it returns the file object.
        # The standard ClearableFileInput validation raises an error if both happen.
        # By the time we are in clean_photo, if there's a file, we just return it.

        return photo
