# links

## Purpose

Turn long URLs into short codes and resolve the codes back.

## Requirements

### Requirement: REQ-LINK-001 Shorten a URL

The system SHALL return a 6-character code of letters and digits for an http or https URL, and the same code every time the same URL is shortened.

#### Scenario: AC-LINK-001.1 A valid URL gets a code

- **WHEN** `shorten("https://example.com/a")` is called
- **THEN** it returns a 6-character code of letters and digits

#### Scenario: AC-LINK-001.2 The same URL keeps its code

- **GIVEN** `shorten("https://example.com/a")` returned code `c`
- **WHEN** `shorten("https://example.com/a")` is called again
- **THEN** it returns `c`

#### Scenario: AC-LINK-001.3 A URL that is not http(s) is rejected

- **WHEN** `shorten("ftp://example.com")` or `shorten("not a url")` is called
- **THEN** it raises `InvalidUrl`

### Requirement: REQ-LINK-002 Resolve a code

The system SHALL return the original URL for a code it issued that has not expired, reject a code it did not issue, and reject an expired code with `ExpiredCode`.

#### Scenario: AC-LINK-002.1 A known code resolves

- **GIVEN** `shorten(url)` returned code `c`
- **WHEN** `resolve(c)` is called
- **THEN** it returns `url`

#### Scenario: AC-LINK-002.2 An unknown code is rejected

- **WHEN** `resolve("zzzzzz")` is called on an empty store
- **THEN** it raises `UnknownCode`

#### Scenario: AC-LINK-002.3 An expired code is rejected

- **GIVEN** `shorten(url, ttl=60)` returned code `c` at time 0
- **WHEN** `resolve(c)` is called at time 60
- **THEN** it raises `ExpiredCode`

### Requirement: REQ-LINK-003 Shorten with a lifetime

The system SHALL accept an optional lifetime in seconds when shortening a URL; the code expires that many seconds after it is issued.

#### Scenario: AC-LINK-003.1 A code resolves before its lifetime ends

- **GIVEN** `shorten(url, ttl=60)` returned code `c` at time 0
- **WHEN** `resolve(c)` is called at time 59
- **THEN** it returns `url`

#### Scenario: AC-LINK-003.2 A lifetime that is not positive is rejected

- **WHEN** `shorten(url, ttl=0)` is called
- **THEN** it raises `ValueError`
