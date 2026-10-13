# World Diabetes Day – Diabetes in Focus

Registration site for World Diabetes Day – Diabetes in Focus, an Internal Medicine Scientific Conference on 15 November 2026 at Semiramis InterContinental Cairo..

## Registration and cPanel deployment

The attendee forms in `index.html` and `registration.html` submit to `register.php`. The PHP endpoint validates the submitted fields and sends the registration details to `wdd-egy@elmawy.com` using PHP `mail()`. It does not use a database, Python, or an external form service. The browser displays success only after PHP reports that the mail handoff was accepted; this does not guarantee final inbox delivery.

For cPanel deployment, upload the site files, including `register.php`, into the domain's document root and enable PHP 7.3 or newer for the domain. The host must permit PHP `mail()` and have a working mail transport configured. Use HTTPS, configure the domain's mail authentication/deliverability settings as directed by the host, and test both successful and rejected submissions on cPanel before relying on the form.

Registration submissions are delivered by email only; they are not stored by the website. Protect the recipient mailbox and follow the organization's approved process for handling participant information.

## Project structure

- `index.html`, `styles.css`, and `app.js` contain the English-language page, responsive design, countdown, poster previews, and registration interactions.
- `server.py` is retained for the existing local Python/SQLite implementation; the cPanel registration flow uses `register.php` instead.
- `assets/topics/` contains the fifteen scientific-theme posters shown on the page.
- `assets/lo2/` contains the ministry marks; `n-cropped.png` is the transparent display version, and `n.jpeg` is retained as the original.
- `ref/` retains the supplied reference artwork. The site uses the conference logo and topic-specific poster copies from `assets/`.
