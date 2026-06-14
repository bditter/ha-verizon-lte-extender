# Changelog

## 1.0.2 - 2026-06-14

- Distinguish connection timeouts, DNS failures, and TCP connection failures
  during setup.
- Add routing-focused setup guidance for Home Assistant hosts on another
  subnet.

## 1.0.1 - 2026-06-14

- Add integration artwork to the Home Assistant `brand` directory.
- Report untrusted/self-signed SSL certificates separately from network errors.
- Clarify that SSL verification should remain disabled for the factory Askey
  certificate.

## 1.0.0 - 2026-06-14

- Add config-flow setup and editable connection options.
- Add automatic SHA-256 login, XSRF handling, and session refresh.
- Add coordinator-based status polling.
- Add status, network, GPS, user-count, and diagnostic sensors.
- Add online, GPS acquired, and in-service binary sensors.
- Keep sensitive identifiers disabled by default.
- Add HACS metadata, artwork, tests, and validation workflow.
