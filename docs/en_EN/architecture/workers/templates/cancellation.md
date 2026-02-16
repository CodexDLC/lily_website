{% raw %}
# 📜 Cancellation Email Template (`cancellation.html`)

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

This Jinja2 template (`cancellation.html`) is used to generate email notifications for cancelled appointments. It extends the `base_email.html` template, providing specific content for the cancellation, including the reason (if provided), appointment details, and an option to book a new appointment.

## Purpose

The `cancellation.html` template informs the recipient that their appointment has been cancelled. It aims to provide necessary details and a clear call to action for rebooking, while maintaining a consistent brand appearance.

## Structure

The template extends `base_email.html` and primarily defines the `{% block content %}` section.

### `{% block title %}`

```html
{% block title %}Terminabsage{% endblock %}
```
Overrides the default title from `base_email.html` to "Terminabsage" (Appointment Cancellation).

### `{% block content %}` Section

This block contains the specific layout and content for the cancellation email.

#### Cancellation Tag

```html
<!-- ТЭГ -->
<tr>
    <td align="center" style="padding-bottom: 20px;">
        <span style="font-family: 'Lato', sans-serif; color: #d9534f; font-size: 12px; letter-spacing: 2px; text-transform: uppercase; font-weight: bold; border-bottom: 1px solid #d9534f; padding-bottom: 5px;">
            TERMINABSAGE
        </span>
    </td>
</tr>
```
A styled text tag indicating "TERMINABSAGE" (APPOINTMENT CANCELLATION), typically in a warning color.

#### Greeting and Standard Message

```html
<!-- ПРИВЕТСТВИЕ -->
<tr>
    <td style="color: #333333; font-family: 'Lato', sans-serif; font-size: 18px; line-height: 1.5; padding-bottom: 20px; text-align: center;">
        <b>{{ greeting }}</b>
    </td>
</tr>
<tr>
    <td style="color: #555555; font-family: 'Lato', sans-serif; font-size: 16px; line-height: 1.6; padding-bottom: 20px; text-align: center;">
        Leider müssen wir Ihren Termin absagen. Wir entschuldigen uns für die Unannehmlichkeiten.
    </td>
</tr>
```
Displays a personalized greeting followed by a standard message of apology for the cancellation.
*   `{{ greeting }}`: Jinja2 variable for the greeting text (e.g., "Sehr geehrte/r [Name]").

#### Cancellation Reason (Optional)

```html
<!-- ПРИЧИНА (Опционально) -->
{% if cancellation_reason %}
<tr>
    <td bgcolor="#fff0f0" style="padding: 15px; border-left: 4px solid #d9534f; border-radius: 4px; margin-bottom: 20px;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%">
            <tr>
                <td style="color: #d9534f; font-family: 'Lato', sans-serif; font-size: 14px; font-weight: bold;">
                    Grund der Absage:
                </td>
            </tr>
            <tr>
                <td style="color: #333333; font-family: 'Lato', sans-serif; font-size: 15px; padding-top: 5px;">
                    {{ cancellation_reason }}
                </td>
            </tr>
        </table>
    </td>
</tr>
{% endif %}
```
An optional block that displays the reason for the cancellation, if provided. It is styled as a warning box.
*   `{% if cancellation_reason %}`: Jinja2 conditional block.
*   `{{ cancellation_reason }}`: Jinja2 variable for the cancellation reason text.

#### Appointment Details

```html
<!-- ДЕТАЛИ -->
<tr>
    <td style="padding-bottom: 30px;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #eeeeee; border-radius: 4px;">
            <tr>
                <td style="padding: 10px 15px; color: #555555; font-family: 'Lato', sans-serif; font-size: 14px;">
                    <b>Behandlung:</b> {{ service_name }} <br>
                    <b>Datum:</b> {{ date }} um {{ time }}
                </td>
            </tr>
        </table>
    </td>
</tr>
```
Displays the details of the cancelled appointment, including the service name, date, and time.
*   `{{ service_name }}`: Jinja2 variable for the name of the service.
*   `{{ date }}`: Jinja2 variable for the date of the appointment.
*   `{{ time }}`: Jinja2 variable for the time of the appointment.

#### Rebooking Button

```html
<!-- Кнопка "Neuen Termin buchen" -->
<tr>
    <td align="center" style="padding-top: 20px;">
        <table border="0" cellspacing="0" cellpadding="0">
            <tr>
                <td align="center" style="border-radius: 5px;" bgcolor="#003831">
                    <a href="{{ link_reschedule }}" target="_blank" style="font-size: 16px; font-family: 'Lato', sans-serif; color: #EDD071; text-decoration: none; padding: 12px 30px; border-radius: 5px; border: 1px solid #EDD071; display: inline-block; font-weight: bold;">
                        Neuen Termin buchen
                    </a>
                </td>
            </tr>
        </table>
    </td>
</tr>
```
A button to book a new appointment, linking to a rescheduling page.
*   `{{ link_reschedule }}`: Jinja2 variable for the rebooking link.

## Jinja2 Variables Used

*   `greeting`: Personalized greeting for the recipient.
*   `cancellation_reason`: Optional text providing the reason for cancellation.
*   `service_name`: The name of the cancelled service.
*   `date`: The date of the cancelled appointment.
*   `time`: The time of the cancelled appointment.
*   `link_reschedule`: URL for booking a new appointment.
{% endraw %}
