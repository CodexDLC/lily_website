notifications =
    .new =
        .booking =
            .title = ✨ <b>Новая запись: { $client_name }</b>
            .details =
                📅 <b>Когда:</b> { $datetime }
                ✂️ <b>Услуга:</b> { $service_name }
                👤 <b>Мастер:</b> { $master_name }
                ────────────────────
                📊 <b>Визиты:</b> { $visits_info }
                💰 <b>Сумма:</b> { $price } €
                { $promo_info }
                📝 <b>Заметка:</b> { $client_notes }

                🆔 <b>ID записи:</b> #{ $id }
            .visits =
                .new = Новый клиент 🆕
                .regular = Постоянный клиент ({ $count }-й визит) ⭐
            .promo = 🎯 <b>Промо:</b> { $title }
        .contact =
            .preview =
                .title = 📋 <b>Новая заявка с сайта</b>
                .text = 📋 <b>Новая заявка с сайта</b>\n\nНажмите «Прочитать» для просмотра.
    .status =
        .block =
            ────────────────────
            📧 <b>Email:</b> { $email_status } { $email_label }
            📱 <b>WhatsApp:</b> { $twilio_status } { $twilio_label }
        .icons =
            .waiting = ⏳
            .sent = ✅
            .success = ✅
            .failed = ❌
            .none = —
        .approved = ✅ ЗАЯВКА ПОДТВЕРЖДЕНА
        .rejected = ❌ ЗАЯВКА ОТКЛОНЕНА
    .btn =
        .approve = ✅ Подтвердить
        .reject = ❌ Отклонить
        .delete = 🗑 Удалить
        .open =
            .crm = 🔗 Открыть в CRM
            .bot = 🤖 Открыть бота
        .read = 📖 Прочитать
        .reply = ✉️ Ответить
    .prompt =
        .reason = Выберите причину отклонения:
    .alert =
        .approved = Заявка подтверждена, письмо отправлено
        .rejected = Заявка отклонена
        .cancelled = Отменено
        .deleted = Сообщение удалено
    .error =
        .api = ⚠️ Ошибка связи с сервером
        .contact =
            .notfound = ⚠️ <b>Текст заявки не найден (устарел).</b>{"\n\n"}Попробуйте найти её в админ-панели.
    .reasons =
        .busy = Мастер занят / Нет времени
        .ill = Мастер заболел
        .materials = Нет материалов
        .blacklist = Клиент в черном списке
