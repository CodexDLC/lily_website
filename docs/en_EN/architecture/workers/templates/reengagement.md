{% raw %}
# 📜 Re-engagement Email Template (`reengagement.html`)

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

This Jinja2 template (`reengagement.html`) is designed to generate emails aimed at re-engaging clients, typically by reminding them to book a new appointment. It extends the `base_email.html` template and provides a personalized message along with a call to action.

## Purpose

The `reengagement.html` template encourages clients who haven't booked recently to return to the salon. It offers a gentle reminder and a direct link to the booking calendar, making it easy for them to schedule their next visit.

## Structure

The template extends `base_email.html` and primarily defines the `{% block content %}` section.

### `{% block title %}`

```html
{% block title %}Zeit für Dich{% endblock %}
```
Overrides the default title from `base_email.html` to "Zeit für Dich" (Time for You).

### `{% block content %}` Section

This block contains the specific layout and content for the re-engagement email.

#### Re-engagement Tag

```html
<!-- ТЭГ -->
<tr>
    <td align="center" style="padding-bottom: 20px;">
        <span style="font-family: 'Lato', sans-serif; color: #003831; font-size: 12px; letter-spacing: 2px; text-transform: uppercase; font-weight: bold; border-bottom: 1px solid #EDD071; padding-bottom: 5px;">
            ZEIT FÜR DICH
        </span>
    </td>
</tr>
```
A styled text tag indicating "ZEIT FÜR DICH" (TIME FOR YOU).

#### Greeting and Body Text

```html
<!-- ПРИВЕТСТВИЕ -->
<tr>
    <td style="color: #333333; font-family: 'Lato', sans-serif; font-size: 18px; line-height: 1.5; padding-bottom: 20px; text-align: center;">
        <b>{{ greeting }}</b>
    </td>
</tr>
<tr>
    <td style="color: #555555; font-family: 'Lato', sans-serif; font-size: 16px; line-height: 1.6; padding-bottom: 30px; text-align: center;">
        {{ body_text }}
    </td>
</tr>
```
Displays a personalized greeting followed by the main body of the re-engagement message.
*   `{{ greeting }}`: Jinja2 variable for the greeting text.
*   `{{ body_text }}`: Jinja2 variable for the main message content.

#### Call to Action Text

```html
<tr>
    <td align="center" style="color: #003831; font-family: 'Playfair Display', serif; font-size: 18px; font-weight: bold; padding-bottom: 20px;">
        Wir haben passende Termine für Sie gefunden:
    </td>
</tr>
```
A call to action text, indicating that suitable appointments have been found.

#### Booking Button

```html
<!-- Кнопка "Anderen Termin wählen" -->
<tr>
    <td align="center" style="padding-top: 20px;">
        <table border="0" cellspacing="0" cellpadding="0">
            <tr>
                <td align="center" style="border-radius: 5px;" bgcolor="#003831">
                    <a href="{{ link_calendar }}" target="_blank" style="font-size: 16px; font-family: 'Lato', sans-serif; color: #EDD071; text-decoration: none; padding: 12px 30px; border-radius: 5px; border: 1px solid #EDD071; display: inline-block; font-weight: bold;">
                        Anderen Termin wählen
                    </a>
                </td>
            </tr>
        </table>
    </td>
</tr>
```
A prominent button that links to the booking calendar, encouraging the client to schedule a new appointment.
*   `{{ link_calendar }}`: Jinja2 variable for the URL of the booking calendar.

## Jinja2 Variables Used

*   `greeting`: Personalized greeting for the recipient.
*   `body_text`: The main body text of the re-engagement message.
*   `link_calendar`: URL for the booking calendar.
{% endraw %}
