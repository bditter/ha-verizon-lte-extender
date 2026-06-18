# Changelog

## 1.0.10 - 2026-06-18

- Rename the In Service binary sensor to Operational Status to match the
  extender web interface.

## 1.0.9 - 2026-06-18

- Keep the GPS Signal entity name and use the concise values `Acquired` and
  `Not acquired`.

## 1.0.8 - 2026-06-18

- Restore the GPS Signal entity name.
- Display its normal values as `Location acquired` or
  `Location not acquired`.

## 1.0.7 - 2026-06-18

- Rename GPS Signal to GPS Acquisition.
- Display normal GPS states as `Acquired` or `Not acquired` instead of raw or
  overly technical values.

## 1.0.6 - 2026-06-18

- Do not treat the always-redacted MDN field as an expired session.
- Limit redacted-session detection to status fields that are populated after a
  successful login, fixing immediate `Session invalid` failures introduced in
  1.0.3.

## 1.0.5 - 2026-06-18

- Clear expired authentication cookies before a forced session refresh.
- Prevent stale `Authtoken` and XSRF cookies from causing `Session invalid`
  during automatic re-login.

## 1.0.4 - 2026-06-18

- Replace raw 4G signal, cell type, GPS signal, and IP mode numbers with
  firmware-defined readable states.
- Remove the IPsec IP and PA temperature entities, including existing entity
  registry entries created by earlier releases.

## 1.0.3 - 2026-06-18

- Detect the firmware's authenticated-data placeholder response as an expired
  session.
- Re-authenticate and retry once when protected status fields are returned as
  `Will display the data after login` despite `result: 1`.

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
