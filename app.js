const forms = document.querySelectorAll('[data-registration-form]');
const countdown = document.querySelector('.countdown-clock');
const themeList = document.querySelector('.theme-list');

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

function setFieldError(form, name, message) {
  const control = form.elements.namedItem(name);
  if (!control) return;
  const field = control.closest('.field, .privacy-check');
  control.setAttribute('aria-invalid', 'true');
  const error = field?.querySelector('.field-error');
  if (error) {
    error.id = `${form.dataset.kind}-${name}-error`;
    error.textContent = message;
    control.setAttribute('aria-describedby', error.id);
  }
}

function clearErrors(form) {
  form.querySelectorAll('[aria-invalid="true"]').forEach((control) => {
    control.removeAttribute('aria-invalid');
    control.removeAttribute('aria-describedby');
  });
  form.querySelectorAll('.field-error').forEach((error) => {
    error.textContent = '';
  });
}

function displayFeedback(form, state, message) {
  const feedback = form.querySelector('.form-feedback');
  feedback.dataset.state = state;
  feedback.textContent = message;
}

forms.forEach((form) => {
  form.addEventListener('input', (event) => {
    if (event.target.matches('input, select, textarea')) {
      event.target.removeAttribute('aria-invalid');
      event.target.removeAttribute('aria-describedby');
      const error = event.target.closest('.field, .privacy-check')?.querySelector('.field-error');
      if (error) error.textContent = '';
    }
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (form.dataset.submitting === 'true') return;
    clearErrors(form);
    const feedback = form.querySelector('.form-feedback');
    feedback.textContent = '';
    feedback.removeAttribute('data-state');

    const payload = Object.fromEntries(new FormData(form).entries());
    payload.kind = form.dataset.kind;
    payload.privacyAccepted = form.elements.namedItem('privacyAccepted').checked;
    const button = form.querySelector('[type="submit"]');
    const originalText = button.innerHTML;
    form.dataset.submitting = 'true';
    button.disabled = true;
    button.innerHTML = '<span class="button-spinner">Submitting…</span>';

    let submitted = false;
    try {
      const response = await fetch(form.action, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const responseText = await response.text();
      let result;
      try {
        result = JSON.parse(responseText);
      } catch {
        throw new Error('The registration service returned an unreadable response. Please try again later.');
      }
      if (!result || typeof result !== 'object') {
        throw new Error('The registration service returned an unexpected response. Please try again later.');
      }
      if (!response.ok || result.accepted !== true) {
        if (result.fields) {
          Object.entries(result.fields).forEach(([name, message]) => setFieldError(form, name, message));
          const firstInvalid = form.querySelector('[aria-invalid="true"]') || form.querySelector('.privacy-check input');
          firstInvalid?.focus();
        }
        throw new Error(result.error || 'We could not process your submission. Please try again.');
      }

      submitted = true;
      displayFeedback(
        form,
        'success',
        result.message || 'Your registration has been submitted. The conference team will follow up.',
      );
    } catch (error) {
      const message = error instanceof TypeError
        ? 'We could not reach the registration service. No confirmation was received. Please try again.'
        : error.message || 'We could not complete your submission. Please try again.';
      displayFeedback(form, 'error', message);
    } finally {
      form.dataset.submitting = 'false';
      button.disabled = submitted;
      if (!submitted) button.innerHTML = originalText;
    }
  });
});
