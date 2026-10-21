# Spec Delta: project

## MODIFIED Requirements

### Requirement: REQ-PROJ-012 Archived changes

The system SHALL list archived changes from the `<date>-<name>` folders of the
archive, oldest first, leaving out folders that are misnamed or whose metadata
cannot be read.

#### Scenario: AC-PROJ-012.1 Listing the archive

- **GIVEN** an archived change, a misnamed folder and a folder with broken metadata in the archive
- **WHEN** archived changes are listed
- **THEN** only the archived change is listed, by its name

#### Scenario: AC-PROJ-012.2 Oldest first

- **GIVEN** changes archived on two different days
- **WHEN** archived changes are listed
- **THEN** the one archived on the earlier day comes first
