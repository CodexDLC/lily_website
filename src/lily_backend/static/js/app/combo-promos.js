(function () {
    function initComboPromos(root) {
        const track = root.querySelector(".combo-promos__track");
        const slides = Array.from(root.querySelectorAll(".combo-promo"));
        const dots = Array.from(root.querySelectorAll(".combo-promos__dot"));
        const prev = root.querySelector("[data-combo-prev]");
        const next = root.querySelector("[data-combo-next]");

        if (!track || slides.length <= 1) return;

        let index = 0;
        let timer = null;

        function goTo(nextIndex) {
            index = (nextIndex + slides.length) % slides.length;
            track.style.transform = `translateX(-${index * 100}%)`;
            slides.forEach((slide, slideIndex) => {
                slide.classList.toggle("combo-promo--active", slideIndex === index);
            });
            dots.forEach((dot, dotIndex) => {
                dot.classList.toggle("combo-promos__dot--active", dotIndex === index);
            });
        }

        function restartTimer() {
            window.clearInterval(timer);
            timer = window.setInterval(() => goTo(index + 1), 6000);
        }

        if (prev) {
            prev.addEventListener("click", () => {
                goTo(index - 1);
                restartTimer();
            });
        }

        if (next) {
            next.addEventListener("click", () => {
                goTo(index + 1);
                restartTimer();
            });
        }

        dots.forEach((dot, dotIndex) => {
            dot.addEventListener("click", () => {
                goTo(dotIndex);
                restartTimer();
            });
        });

        restartTimer();
    }

    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll("[data-combo-promos]").forEach(initComboPromos);
    });
})();
