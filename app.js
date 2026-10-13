const countdown = document.querySelector('.countdown-clock');
const themeList = document.querySelector('.theme-list');

document.querySelectorAll('form[action="https://formsubmit.co/wdd-egy@elmawy.com"] [name="_next"]')
  .forEach((redirect) => {
    redirect.value = `${window.location.origin}/thank-you.html`;
  });

if (themeList) {
  const closePreviews = (except) => {
    themeList.querySelectorAll('.theme-image-trigger[aria-expanded="true"]').forEach((trigger) => {
      if (trigger !== except) trigger.setAttribute('aria-expanded', 'false');
    });
  };

  themeList.addEventListener('click', (event) => {
    const trigger = event.target.closest('.theme-image-trigger');
    if (!trigger) return;
    const open = trigger.getAttribute('aria-expanded') !== 'true';
    closePreviews();
    trigger.setAttribute('aria-expanded', String(open));
  });

  themeList.addEventListener('focusin', (event) => {
    const trigger = event.target.closest('.theme-image-trigger');
    if (trigger?.matches(':focus-visible')) {
      closePreviews(trigger);
      trigger.setAttribute('aria-expanded', 'true');
    }
  });

  themeList.addEventListener('focusout', (event) => {
    const trigger = event.target.closest('.theme-image-trigger');
    if (trigger && !trigger.contains(event.relatedTarget)) {
      trigger.setAttribute('aria-expanded', 'false');
    }
  });

  document.addEventListener('pointerdown', (event) => {
    if (!event.target.closest('.theme-image-trigger')) closePreviews();
  });

  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    const openTrigger = themeList.querySelector('.theme-image-trigger[aria-expanded="true"]');
    if (!openTrigger) return;
    closePreviews();
    openTrigger.focus();
  });
}

if (countdown) {
  const eventDate = new Date('2026-11-15T00:00:00+02:00').getTime();
  let countdownInterval;
  const units = {
    days: countdown.querySelector('[data-countdown-days]'),
    hours: countdown.querySelector('[data-countdown-hours]'),
    minutes: countdown.querySelector('[data-countdown-minutes]'),
    seconds: countdown.querySelector('[data-countdown-seconds]'),
  };
  const formatNumber = new Intl.NumberFormat('en', {
    minimumIntegerDigits: 2,
    useGrouping: false,
  });

  const updateCountdown = () => {
    const remaining = Math.max(0, eventDate - Date.now());
    const totalSeconds = Math.floor(remaining / 1000);
    units.days.textContent = formatNumber.format(Math.floor(totalSeconds / 86400));
    units.hours.textContent = formatNumber.format(Math.floor((totalSeconds % 86400) / 3600));
    units.minutes.textContent = formatNumber.format(Math.floor((totalSeconds % 3600) / 60));
    units.seconds.textContent = formatNumber.format(totalSeconds % 60);

    if (remaining === 0) {
      countdown.setAttribute('aria-label', 'The conference date has arrived');
      window.clearInterval(countdownInterval);
    }
    return remaining > 0;
  };

  if (updateCountdown()) {
    countdownInterval = window.setInterval(updateCountdown, 1000);
  }
}
