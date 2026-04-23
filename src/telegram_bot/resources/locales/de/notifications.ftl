notifications =
    .new =
        .booking =
            .title = ✨ <b>Neue Buchung: { $client_name }</b>
            .details =
                📅 <b>Wann:</b> { $datetime }
                ✂️ <b>Dienstleistung:</b> { $service_name }
                👤 <b>Master:</b> { $master_name }
                ────────────────────
                📊 <b>Besuche:</b> { $visits_info }
                💰 <b>Summe:</b> { $price } €
                { $promo_info }
                📝 <b>Notiz:</b> { $client_notes }

                🆔 <b>Buchungs-ID:</b> #{ $id }
            .visits =
                .new = Neuer Kunde 🆕
                .regular = Stammkunde ({ $count }. Besuch) ⭐
            .promo = 🎯 <b>Promo:</b> { $title }
        .contact =
            .preview =
                .title = 📋 <b>Neue Website-Anfrage</b>
                .text = 📋 <b>Neue Website-Anfrage</b>\n\nKlicken Sie auf „Lesen“, um sie anzuzeigen.
    .status =
        .block =
            ────────────────────
            📧 <b>E-Mail:</b> { $email_status } { $email_label }
            📱 <b>WhatsApp:</b> { $twilio_status } { $twilio_label }
        .icons =
            .waiting = ⏳
            .sent = ✅
            .success = ✅
            .failed = ❌
            .none = —
        .approved = ✅ ANFRAGE BESTÄTIGT
        .rejected = ❌ ANFRAGE ABGELEHNT
    .btn =
        .approve = ✅ Bestätigen
        .reject = ❌ Ablehnen
        .delete = 🗑 Löschen
        .open =
            .crm = 🔗 Im CRM öffnen
            .bot = 🤖 Bot öffnen
        .read = 📖 Lesen
        .reply = ✉️ Antworten
    .prompt =
        .reason = Grund für die Ablehnung wählen:
    .alert =
        .approved = Anfrage bestätigt, E-Mail gesendet
        .rejected = Anfrage abgelehnt
        .cancelled = Abgebrochen
        .deleted = Nachricht gelöscht
    .error =
        .api = ⚠️ Server-Verbindungsfehler
        .contact =
            .notfound = ⚠️ <b>Anfragetext nicht gefunden (veraltet).</b>{"\n\n"}Bitte suchen Sie in der Admin-Konsole danach.
    .reasons =
        .busy = Master belegt / Keine Zeit
        .ill = Master ist krank
        .materials = Keine Materialien
        .blacklist = Kunde auf der Blacklist
