notifications-new-booking-title = ✨ <b>Новая запись: { $client_name }</b>

notifications-new-booking-details =
    📅 <b>Когда:</b> { $datetime }
    ✂️ <b>Услуга:</b> { $service_name }
    👤 <b>Мастер:</b> { $master_name }
    ────────────────────
    📊 <b>Визиты:</b> { $visits_info }
    💰 <b>Сумма:</b> { $price } €
    { $promo_info }
    📝 <b>Заметка:</b> { $client_notes }

    🆔 <b>ID записи:</b> #{ $id }

notifications-new-booking-visits-new = Новый клиент 🆕
notifications-new-booking-visits-regular = Постоянный клиент ({ $count }-й визит) ⭐
notifications-new-booking-promo = 🎯 <b>Промо:</b> { $title }

notifications-new-contact-preview-title = 📋 <b>Новая заявка с сайта</b>
notifications-new-contact-preview-text =
    📋 <b>Новая заявка с сайта</b>

    Нажмите «Прочитать» для просмотра.

notifications-status-block =
    ────────────────────
    📧 <b>Email:</b> { $email_status } { $email_label }
    📱 <b>WhatsApp:</b> { $twilio_status } { $twilio_label }

notifications-status-icons-waiting = ⏳
notifications-status-icons-sent = ✅
notifications-status-icons-success = ✅
notifications-status-icons-failed = ❌
notifications-status-icons-none = —

notifications-status-approved = ✅ ЗАЯВКА ПОДТВЕРЖДЕНА
notifications-status-rejected = ❌ ЗАЯВКА ОТКЛОНЕНА

notifications-btn-approve = ✅ Подтвердить
notifications-btn-reject = ❌ Отклонить
notifications-btn-delete = 🗑 Удалить
notifications-btn-open-crm = 🔗 Открыть в CRM
notifications-btn-open-bot = 🤖 Открыть бота
notifications-btn-read = 📖 Прочитать
notifications-btn-reply = ✉️ Ответить

notifications-prompt-reason = Выберите причину отклонения:

notifications-alert-approved = Заявка подтверждена, письмо отправлено
notifications-alert-rejected = Заявка отклонена
notifications-alert-cancelled = Отменено
notifications-alert-deleted = Сообщение удалено

notifications-error-api = ⚠️ Ошибка связи с сервером (ID: { $booking_id })
notifications-error-contact-notfound = ⚠️ <b>Текст заявки не найден (устарел).</b>

    Попробуйте найти её в админ-панели.

notifications-reasons-busy = Мастер занят / Нет времени
notifications-reasons-ill = Мастер заболел
notifications-reasons-materials = Нет материалов
notifications-reasons-blacklist = Клиент в черном списке
