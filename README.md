# World Diabetes Day – Diabetes in Focus

Registration site for World Diabetes Day – Diabetes in Focus, an Internal Medicine Scientific Conference on 15 November 2026 at Semiramis InterContinental Cairo..

## Run locally

Requires Python 3.10 or newer. Start the app from the project directory:

```sh
python3 server.py
```

Open [http://localhost:8000](http://localhost:8000). Set `HOST` or `PORT` to change the bind address.

## Project structure

- `index.html`, `styles.css`, and `app.js` contain the English-language page, responsive design, countdown, poster previews, and registration interactions.
- `server.py` serves the site and handles attendee and sponsorship submissions at `/api/registrations`.
- `assets/topics/` contains the fifteen scientific-theme posters shown on the page.
- `assets/lo2/` contains the ministry marks; `n-cropped.png` is the transparent display version, and `n.jpeg` is retained as the original.
- `ref/` retains the supplied reference artwork. The site uses the conference logo and topic-specific poster copies from `assets/`.

## Registration storage

Validated attendee registrations and sponsorship inquiries are stored in `var/registrations.sqlite3`. The database is not exposed through the web server and is excluded from git. Back up that file using the organization's approved secure storage process. No submissions are stored in the browser or exposed in a public listing.

The app creates the database automatically. Keep the database and its containing directory restricted to the server account; the app attempts to set Unix permissions accordingly.

## Email delivery

Email is optional and is not active until SMTP credentials have been configured in the server environment. Set `SMTP_HOST` and `SMTP_FROM`; optionally set `SMTP_PORT` (default `587`), `SMTP_USERNAME`, and `SMTP_PASSWORD`. STARTTLS is enabled by default for ports other than `465`; set `SMTP_STARTTLS=false` only when the mail relay explicitly requires plaintext transport. Port `465` uses implicit TLS.

When SMTP is configured, each accepted submission sends a notice to `wdd-egy@elmawy.com` and a confirmation to the submitter. An SMTP failure does not discard a submission already committed to the database; the page reports that notifications need attention. Never put SMTP credentials in client-side files or commit them to git.

## Deployment

Run behind a maintained HTTPS reverse proxy and use a persistent, access-controlled volume for `WDD_DATABASE` in production. Set `HOST` and `PORT` as required by the host. The included rate limit is process-local; use an edge/WAF rate limit as well when deploying multiple workers or instances. Configure and test SMTP delivery and database backups in the target environment before announcing email confirmations or production availability.