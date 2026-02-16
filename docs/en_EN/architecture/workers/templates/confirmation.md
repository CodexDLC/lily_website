{% raw %}
# 📜 Confirmation Email Template (`confirmation.html`)

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

This Jinja2 template (`confirmation.html`) is used to generate email notifications for confirmed appointments. It extends the `base_email.html` template, providing specific content for the confirmation, including a greeting, a thank you message, and detailed appointment information.

## Purpose

The `confirmation.html` template serves to officially confirm a client's booking, providing them with all the essential details of their appointment in a clear and branded format.

## Structure

The template extends `base_email.html` and primarily defines the `{% block content %}` section.

### `{% block title %}`

```html
{% block title %}Terminbestätigung{% endblock %}
```
Overrides the default title from `base_email.html` to "Terminbestätigung" (Appointment Confirmation).

### `{% block content %}` Section

This block contains the specific layout and content for the confirmation email.

#### Confirmation Tag

```html
<!-- ТЭГ -->
<tr>
    <td align="center" style="padding-bottom: 20px;">
        <span style="font-family: 'Lato', sans-serif; color: #003831; font-size: 12px; letter-spacing: 2px; text-transform: uppercase; font-weight: bold; border-bottom: 1px solid #EDD071; padding-bottom: 5px;">
            TERMINBESTÄTIGUNG
        </span>
    </td>
</tr>
```
A styled text tag indicating "TERMINBESTÄTIGUNG" (APPOINTMENT CONFIRMATION).

#### Greeting and Thank You Message

```html
<!-- ПРИВЕТСТВИЕ -->
<tr>
    <td style="color: #333333; font-family: 'Lato', sans-serif; font-size: 18px; line-height: 1.5; padding-bottom: 20px; text-align: center;">
        <b>{{ greeting }}</b>
    </td>
</tr>
<tr>
    <td style="color: #555555; font-family: 'Lato', sans-serif; font-size: 16px; line-height: 1.6; padding-bottom: 30px; text-align: center;">
        Vielen Dank für Ihre Buchung. Ihr Termin wurde успешно bestätigt. Wir freuen uns darauf, Sie bei uns begrüßen zu dürfen.
    </td>
</tr>
```
Displays a personalized greeting followed by a thank you message and confirmation of the booking.
*   `{{ greeting }}`: Jinja2 variable for the greeting text (e.g., "Sehr geehrte/r [Name]").

#### Appointment Details

```html
<!-- ДЕТАЛИ -->
<tr>
    <td bgcolor="#f9f9f9" style="padding: 20px; border-left: 4px solid #003831; border-radius: 4px;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%">
            <tr>
                <td width="30%" style="color: #003831; font-family: 'Lato', sans-serif; font-size: 14px; font-weight: bold; padding-bottom: 10px;">Behandlung:</td>
                <td style="color: #333333; font-family: 'Lato', sans-serif; font-size: 14px; padding-bottom: 10px;">{{ service_name }}</td>
            </tr>
            <tr>
                <td width="30%" style="color: #003831; font-family: 'Lato', sans-serif; font-size: 14px; font-weight: bold; padding-bottom: 10px;">Datum:</td>
                <td style="color: #333333; font-family: 'Lato', sans-serif; font-size: 14px; padding-bottom: 10px;">{{ date }}</td>
            </tr>
            <tr>
                <td style="color: #003831; font-family: 'Lato', sans-serif; font-size: 14px; font-weight: bold;">Uhrzeit:</td>
                <td style="color: #333333; font-family: 'Lato', sans-serif; font-size: 14px;">{{ time }}</td>
            </tr>
        </table>
    </td>
</tr>
```
Displays the confirmed appointment details in a structured box, including the service name, date, and time.
*   `{{ service_name }}`: Jinja2 variable for the name of the booked service.
*   `{{ date }}`: Jinja2 variable for the date of the appointment.
*   `{{ time }}`: Jinja2 variable for the time of the appointment.

## Jinja2 Variables Used

*   `greeting`: Personalized greeting for the recipient.
*   `service_name`: The name of the booked service.
*   `date`: The date of the booked appointment.
*   `time`: The time of the booked appointment.
{% endraw %}
