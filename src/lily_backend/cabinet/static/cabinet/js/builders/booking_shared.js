/* CODEX_DJANGO_CLI BLUEPRINT STATUS: MOVE_TO_CLI_BLUEPRINT. Reason: generated cabinet app asset source for codex-django-cli blueprints. */
/* @provides cabinet.builders.booking_shared
   @depends cabinet.widgets.date_time_picker, cabinet.widgets.tabbed_assignment */
(function (window) {
    window.CabinetBookingBuilders = window.CabinetBookingBuilders || {};

    window.CabinetBookingBuilders.createDayLookupMaps = function createDayLookupMaps(days) {
        const dayLabels = {};
        const dayMonthKeys = {};
        const monthLabels = {};
        const monthKeys = [];

        (days || []).forEach((day) => {
            dayLabels[day.iso] = day.label;
            dayMonthKeys[day.iso] = day.month_key;
            if (!monthLabels[day.month_key]) {
                monthLabels[day.month_key] = day.month_label;
                monthKeys.push(day.month_key);
            }
        });

        return { dayLabels, dayMonthKeys, monthLabels, monthKeys };
    };
})(window);
