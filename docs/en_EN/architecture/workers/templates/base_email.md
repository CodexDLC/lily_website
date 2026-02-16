{% raw %}
# 📜 Base Email Template (`base_email.html`)

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

This Jinja2 template (`base_email.html`) serves as the foundational HTML structure for all email notifications sent by the workers. It provides a consistent design, responsive styling, and common elements like a header with a logo and a footer with legal links and a disclaimer.

## Purpose

The `base_email.html` template ensures that all outgoing emails have a unified look and feel, reducing redundancy and simplifying the creation of new email types. It includes:
*   Basic HTML5 structure.
*   Inline CSS for cross-client compatibility and responsiveness.
*   A customizable header with a logo.
*   A content block for injecting specific email content.
*   A standard footer with copyright and legal links.

## Structure

The template is a standard HTML document with embedded Jinja2 syntax for dynamic content.

### `<head>` Section

Contains metadata, a dynamic title block, and inline CSS for styling and responsiveness.

*   `{% block title %}`: A Jinja2 block that allows child templates to override the email's title. The default title is "Lily Beauty Salon".
*   **Inline CSS**: Includes general styles for email clients and media queries (`@media screen and (max-width: 525px)`) for responsive behavior on smaller screens.

### `<body>` Section

The main body of the email, structured using nested tables for maximum compatibility across various email clients.

#### Header Section

```html
<td align="center" bgcolor="#003831" style="padding: 25px 0 20px 0; border-radius: 8px 8px 0 0;">
    <a href="{{ site_url }}" target="_blank" style="text-decoration: none;">
        <img src="{{ logo_url | default('https://pinlite.dev/media/storage/a3/65/a365b5fedad7fb5779bc5fcf63f00ebc19ed90808c4010a0fbec7207773ca95e.png') }}" alt="LILY BEAUTY SALON" width="180" style="display: block; font-family: 'Playfair Display', serif; color: #EDD071; font-size: 24px;" border="0">
    </a>
</td>
```
*   **Background**: Dark green (`#003831`).
*   **Logo**: An `<img>` tag displaying the salon's logo.
    *   `{{ logo_url | default(...) }}`: A Jinja2 variable that inserts the URL of the logo. If `logo_url` is not provided in the context, it defaults to a specific Pinlite URL.
    *   The logo is wrapped in an `<a>` tag linking to `{{ site_url }}`.
*   **`site_url`**: A Jinja2 variable expected to contain the base URL of the website.

#### Content Block

```html
{% block content %}{% endblock %}
```
This is the primary area where specific email content from child templates will be injected. Child templates will define their own `{% block content %}` to fill this section.

#### Footer Section

```html
<td bgcolor="#f4f4f4" align="center" style="padding: 30px 0 30px 0; color: #888888; font-family: 'Lato', sans-serif; font-size: 12px;">
    <p style="margin: 0;">© 2023 Lily Beauty Salon. Alle Rechte vorbehalten.</p>
    <p style="margin: 10px 0 0 0;">
        <a href="{{ site_url }}" style="color: #003831; text-decoration: none;">Website</a> |
        <a href="{{ site_url }}/legal/impressum" style="color: #003831; text-decoration: none;">Impressum</a> |
        <a href="{{ site_url }}/legal/datenschutz" style="color: #003831; text-decoration: none;">Datenschutz</a>
    </p>
    <p style="margin: 15px 0 0 0; color: #a0a0a0;">
        Dies ist eine automatisch generierte E-Mail. Bitte antworten Sie nicht direkt auf diese Nachricht.
        Bei Fragen oder Anliegen nutzen Sie bitte unser <a href="{{ site_url }}{{ url_path_contact_form }}" style="color: #003831; text-decoration: underline;">Kontaktformular</a>.
    </p>
</td>
```
*   **Copyright**: Static copyright information.
*   **Legal Links**: Links to the website, impressum, and data privacy pages.
    *   `{{ site_url }}`: Used again for the website link.
    *   `{{ url_path_contact_form }}`: A Jinja2 variable expected to contain the path to the contact form, appended to `site_url`.
*   **Disclaimer**: A standard message indicating the email is automatically generated and provides a link to a contact form.

## Jinja2 Variables Used

*   `site_url`: The base URL of the website.
*   `logo_url`: The URL of the logo image (with a default fallback).
*   `url_path_contact_form`: The path to the contact form.
{% endraw %}
