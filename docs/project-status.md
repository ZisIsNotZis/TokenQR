# TokenQR project status

## Classification

Closed proof-of-concept: an open, client-first token-authorization protocol, plus
a single-page web POC and a local Relay.

## Status

Closed as a POC (2026-09-29). The minimal authorization loop is implemented and
demonstrable; the unchecked roadmap items are optional future extensions, not
required for the POC. No further development is planned unless the project's
inputs or goals change.

## Evidence

- Protocol draft: [`protocol.md`](protocol.md).
- POC UI: [`../tokenqr.html`](../tokenqr.html) (computer + provider tabs, QR
  generation and camera scan, P-256 ECDH + HKDF + AES-GCM, policy display) and
  [`../reverse.html`](../reverse.html) (relay-free reverse authorization).
- Local Relay: [`../server.py`](../server.py); optional Gateway assets under
  `../gateway/`.

## Deferred (optional future roadmap)

Public Relay adapter, provider model-list cache/editing, a LiteLLM-style Gateway
adaptor, and independent protocol implementations with interop tests. These are
extensions beyond the minimal closed loop.
