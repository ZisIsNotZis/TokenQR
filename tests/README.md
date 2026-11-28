# TokenQR local acceptance

Run from the repository root with Python 3.10+, Node 18+, Playwright, and Chromium:

```sh
npm install --no-save --package-lock=false playwright
npx playwright install chromium
python3 tests/consent_fixture.py
```

If tools are already installed elsewhere, set `PLAYWRIGHT_MODULE` to the absolute
path of Playwright’s `index.mjs` and `CHROME_BIN` to a compatible Chromium or
Chrome headless-shell executable. An optional final argument is a directory for
consent screenshots, e.g. `python3 tests/consent_fixture.py /tmp/tokenqr-consent`.

The fixture binds two ephemeral `127.0.0.1` ports. It serves the checkout, runs
`server.py`’s actual Relay handler without starting its public listener, and
answers Chat Completions with a fixed synthetic response. The test uses fresh,
separate receiver and Provider browser contexts, blocks service workers, and
aborts page requests to other origins. It does not need accounts, a camera,
a public Relay, or a real provider token.

The QR contents are copied using the Provider’s labeled paste input. The
390×844 receiver must not scroll horizontally after rendering the QR and its
text. At both viewport sizes (1280×720 and 390×844), the decision buttons must
be fully in view and hit-testable on first
open. The test clicks their measured screen coordinates so Playwright cannot
scroll an off-screen control into view. Approval must send an encrypted Relay
payload and allow the receiver to make the expected mock chat request. Decline
must send no approval POST; the next receiver poll must stay empty. A narrow
stress case also exercises a long purpose and a large advanced model list,
checking that the body scrolls vertically without horizontal overflow and the
decision buttons stay reachable.
