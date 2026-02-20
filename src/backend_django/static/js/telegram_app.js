document.addEventListener("DOMContentLoaded", function () {
    // Make sure Telegram WebApp is available
    if (!window.Telegram || !window.Telegram.WebApp) {
        console.error("Telegram WebApp API not found.");
        return;
    }

    const tg = window.Telegram.WebApp;
    const form = document.getElementById('reply-form');

    // If we're not on the reply form page, just initialize and return
    if (!form) return;

    const replyInput = document.getElementById('reply_text');
    const subjectInput = document.getElementById('subject');
    const reqId = document.getElementById('req_id').value;

    // Setup MainButton
    tg.MainButton.setText("SEND REPLY");
    tg.MainButton.color = tg.themeParams.button_color || '#2481cc';
    tg.MainButton.textColor = tg.themeParams.button_text_color || '#ffffff';
    tg.MainButton.show();
    tg.MainButton.disable();

    // Validate input to enable/disable button
    function checkInputs() {
        if (replyInput.value.trim().length > 0 && subjectInput.value.trim().length > 0) {
            tg.MainButton.enable();
        } else {
            tg.MainButton.disable();
        }
    }

    replyInput.addEventListener('input', checkInputs);
    subjectInput.addEventListener('input', checkInputs);

    // On Button Click
    tg.MainButton.onClick(function() {
        if (!replyInput.value.trim()) return;

        tg.showConfirm("Send this reply?", function(confirmed) {
            if (confirmed) {
                submitForm();
            }
        });
    });

    function submitForm() {
        // Show loading spinner on MainButton
        tg.MainButton.showProgress();

        const payload = {
            req_id: reqId,
            subject: subjectInput.value.trim(),
            reply_text: replyInput.value.trim(),
            initData: tg.initData
        };

        const actionUrl = window.location.pathname + window.location.search;

        fetch(actionUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Telegram-Init-Data': tg.initData
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            tg.MainButton.hideProgress();

            if (data.status === 'success') {
                document.getElementById('form-container').classList.add('hidden');
                document.getElementById('success-message').classList.remove('hidden');
                tg.MainButton.hide();
                tg.HapticFeedback.notificationOccurred('success');

                setTimeout(() => {
                    tg.close();
                }, 2500);
            } else {
                tg.HapticFeedback.notificationOccurred('error');
                tg.showAlert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error("Fetch error:", error);
            tg.MainButton.hideProgress();
            tg.HapticFeedback.notificationOccurred('error');
            tg.showAlert('Network Error occurred while sending.');
        });
    }
});
