notifications-new-booking-title = ✨ <b>Neue Buchung: { $client_name }</b>

notifications-new-booking-details =
    📅 <b>Wann:</b> { $datetime }
    ✂️ <b>Dienstleistung:</b> { $service_name }
    👤 <b>Master:</b> { $master_name }
    ────────────────────
    📊 <b>Besuche:</b> { $visits_info }
    💰 <b>Summe:</b> { $price } €
    { $promo_info }
    📝 <b>Notiz:</b> { $client_notes }

    🆔 <b>Buchungs-ID:</b> #{ $id }

notifications-new-booking-visits-new = Neuer Kunde 🆕
notifications-new-booking-visits-regular = Stammkunde ({ $count }. Besuch) ⭐
notifications-new-booking-promo = 🎯 <b>Promo:</b> { $title }

notifications-new-contact-preview-title = 📋 <b>Neue Website-Anfrage</b>
notifications-new-contact-preview-text =
    📋 <b>Neue Website-Anfrage</b>

    Klicken Sie auf „Lesen", um sie anzuzeigen.

notifications-status-block =
    ────────────────────
    📧 <b>E-Mail:</b> { $email_status } { $email_label }
    📱 <b>WhatsApp:</b> { $twilio_status } { $twilio_label }

notifications-status-icons-waiting = ⏳
notifications-status-icons-sent = ✅
notifications-status-icons-success = ✅
notifications-status-icons-failed = ❌
notifications-status-icons-none = —

notifications-status-approved = ✅ ANFRAGE BESTÄTIGT
notifications-status-rejected = ❌ ANFRAGE ABGELEHNT

notifications-btn-approve = ✅ Bestätigen
notifications-btn-reject = ❌ Ablehnen
notifications-btn-delete = 🗑 Löschen
notifications-btn-open-crm = 🔗 Im CRM öffnen
notifications-btn-open-bot = 🤖 Bot öffnen
notifications-btn-read = 📖 Lesen
notifications-btn-reply = ✉️ Antworten

notifications-prompt-reason = Grund für die Ablehnung wählen:

notifications-alert-approved = Anfrage bestätigt, E-Mail gesendet
notifications-alert-rejected = Anfrage abgelehnt
notifications-alert-cancelled = Abgebrochen
notifications-alert-deleted = Nachricht gelöscht

notifications-error-api = ⚠️ Server-Verbindungsfehler (ID: { $booking_id })
notifications-error-contact-notfound = ⚠️ <b>Anfragetext nicht gefunden (veraltet).</b>

    Bitte suchen Sie in der Admin-Konsole danach.

notifications-reasons-busy = Master belegt / Keine Zeit
notifications-reasons-ill = Master ist krank
notifications-reasons-materials = Keine Materialien
notifications-reasons-blacklist = Kunde auf der Blacklist
