# World Diabetes Day – Diabetes in Focus

Registration site for World Diabetes Day – Diabetes in Focus, an Internal Medicine Scientific Conference on 15 November 2026 at Semiramis InterContinental Cairo..

## Registration and cPanel deployment

The attendee forms in `index.html` and `registration.html` submit directly to FormSubmit at `wdd-egy@elmawy.com`. Client-side JavaScript sets the `_next` redirect to the current origin's `thank-you.html` page. Registration does not use a database, Python handler, or PHP mail endpoint.

For deployment, upload the site files to the hosting document root and use HTTPS. Complete FormSubmit's email activation for the recipient address and test delivery after deployment.

Registration submissions are delivered by email only; they are not stored by the website. Protect the recipient mailbox and follow the organization's approved process for handling participant information.

## Project structure

- `index.html`, `styles.css`, and `app.js` contain the English-language page, responsive design, countdown, poster previews, and registration interactions.
- `server.py` can serve the static site locally; it does not handle registration. Registration forms submit directly to FormSubmit.
- `assets/topics/` contains the fifteen scientific-theme posters shown on the page.
- `assets/lo2/` contains the ministry marks; `n-cropped.png` is the transparent display version, and `n.jpeg` is retained as the original.
- `ref/` retains the supplied reference artwork. The site uses the conference logo and topic-specific poster copies from `assets/`.
