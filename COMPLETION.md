# Completion — minimal authorization POC

Accepted on 2026-11-29.

TokenQR completes the local TQR1 consent path. A local app generates a QR
request, and a provider page in a separate browser context displays the request
and lets the user approve or decline. Approval sends ciphertext through the
loopback relay. The app decrypts the grant and makes a simulated Chat
Completions request. Decline sends no approval and leaves the next poll empty.

An independent acceptance run imported the frozen candidate from baseline `622b4d08` and ran
`python3 tests/consent_fixture.py` with Chrome for Testing 157.0.8103.78. All five
scenarios passed. They covered approval and decline at 1280×720 and 390×844, and
a long request at 390×844. The fixed-screen coordinate clicks confirmed that
both choices were usable when the dialog opened.

- [Run the local acceptance suite](tests/README.md)
- [Read the independent browser review](docs/review/consent.md)
- [See the verified scope and remaining limits](docs/project-status.md)

The browser handoff uses pasted QR contents and synthetic credentials. Camera
scanning, physical devices, interoperability, real providers, reverse
authorization, and the optional gateway were outside the completed POC.
