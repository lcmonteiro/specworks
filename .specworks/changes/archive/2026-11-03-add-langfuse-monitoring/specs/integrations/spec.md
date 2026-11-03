# Spec Delta: integrations

## ADDED Requirements

### Requirement: REQ-INTEG-008 Langfuse settings

The system SHALL treat telemetry as `on` when the top level's config sets
`telemetry.langfuse: true` and both `SPECWORKS_LANGFUSE_PUBLIC_KEY` and
`SPECWORKS_LANGFUSE_SECRET_KEY` are set and not empty, as `keys missing` when
the config opts in but a key is missing, and as `off` otherwise. The host SHALL
be `SPECWORKS_LANGFUSE_HOST` when set, else `telemetry.host`, else
`https://cloud.langfuse.com`. The unprefixed `LANGFUSE_*` variables SHALL be
ignored. The keys' values SHALL never appear in any output, error or file
written by specworks.

#### Scenario: AC-INTEG-008.1 On

- **GIVEN** a config with `telemetry.langfuse: true` and both keys set in the environment
- **WHEN** the settings are read
- **THEN** telemetry is `on` with the host `https://cloud.langfuse.com`

#### Scenario: AC-INTEG-008.2 Keys missing

- **GIVEN** a config with `telemetry.langfuse: true`, and `SPECWORKS_LANGFUSE_SECRET_KEY` unset or empty
- **WHEN** the settings are read
- **THEN** telemetry is `keys missing`

#### Scenario: AC-INTEG-008.3 Not opted in

- **GIVEN** both keys set in the environment, and a config with no `telemetry` block or `telemetry.langfuse: false`
- **WHEN** the settings are read
- **THEN** telemetry is `off`

#### Scenario: AC-INTEG-008.4 The host

- **GIVEN** a config with `telemetry.host: https://a.example.com`
- **WHEN** the settings are read with `SPECWORKS_LANGFUSE_HOST=https://b.example.com`, then without it
- **THEN** the host is `https://b.example.com`, then `https://a.example.com`

#### Scenario: AC-INTEG-008.5 The plain Langfuse variables are ignored

- **GIVEN** a config with `telemetry.langfuse: true` and `telemetry.host: https://a.example.com`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` and `LANGFUSE_HOST=https://b.example.com` set, and no `SPECWORKS_LANGFUSE_*` variable
- **WHEN** the settings are read
- **THEN** telemetry is `keys missing` and the host is `https://a.example.com`

### Requirement: REQ-INTEG-009 Sending a change's events

When telemetry is `on`, the system SHALL send the lines of a change's
`events.jsonl` after the count held in its `events.sent` (0 when there is
none) to `<host>/api/public/ingestion` with basic authentication from the
public and secret keys, in batches of at most 100 events: each batch holds the
change's trace (its trace ID, its ref as name and as session ID) and one event
per line with the line's `event` as name, its `at` as time and its other
fields as metadata. After each batch the server accepts (a 2xx response), it
SHALL add that batch's count to `events.sent`. A batch that fails (no
connection, no answer within 5 seconds, or another status) SHALL stop the
sending, leave the rest unsent and give the reason, without raising. With
nothing unsent, it SHALL make no request. It SHALL return how many events were
sent and how many are still queued.

#### Scenario: AC-INTEG-009.1 Only the unsent events

- **GIVEN** a change with 5 lines in `events.jsonl` and `events.sent` holding 3, and a server that accepts every batch
- **WHEN** its events are sent
- **THEN** the server gets one batch with the change's trace and the last 2 events, authenticated with the keys, `events.sent` holds 5, and the result is 2 sent and 0 queued

#### Scenario: AC-INTEG-009.2 The server refuses

- **GIVEN** a change with 4 unsent events and a server that answers 500
- **WHEN** its events are sent
- **THEN** no error is raised, `events.sent` is unchanged, and the result is 0 sent, 4 queued, with a reason naming the status

#### Scenario: AC-INTEG-009.3 No answer

- **GIVEN** a change with unsent events, and a host that accepts the connection but never answers
- **WHEN** its events are sent
- **THEN** it returns within about 5 seconds with 0 sent, the events still queued, and a reason saying it timed out

#### Scenario: AC-INTEG-009.4 Nothing to send

- **GIVEN** a change whose `events.sent` equals its number of lines, or with no `events.jsonl`
- **WHEN** its events are sent
- **THEN** no request is made and the result is 0 sent, 0 queued

#### Scenario: AC-INTEG-009.5 Many events

- **GIVEN** a change with 250 unsent events, and a server that accepts the first two batches and answers 500 to the third
- **WHEN** its events are sent
- **THEN** the server gets batches of 100, 100 and 50 events, `events.sent` holds 200, and the result is 200 sent and 50 queued

#### Scenario: AC-INTEG-009.6 The keys stay secret

- **GIVEN** keys `pk-test` and `sk-test`, and a server that answers 401
- **WHEN** a change's events are sent
- **THEN** the reason names the status and holds neither `pk-test` nor `sk-test`
