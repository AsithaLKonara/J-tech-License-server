Feature: Pattern JSON Schema
  As a developer
  I want to use the canonical JSON schema for patterns
  So that patterns are portable and validated

  Background:
    Given I have a Pattern object

  Scenario: Convert pattern to JSON
    When I convert the pattern to JSON with RLE encoding
    Then JSON should be valid according to schema v1.0
    And JSON should contain required fields: "schema_version", "id", "name", "matrix", "frames"
    And JSON schema_version should be "1.0"

  Scenario: Convert JSON to pattern
    Given I have valid pattern JSON conforming to schema v1.0
    When I convert JSON to Pattern object
    Then Pattern should be created successfully
    And Pattern should match original dimensions
    And Pattern should have correct frame count

  Scenario: Round-trip conversion
    Given I have a Pattern object
    When I convert Pattern to JSON and back to Pattern
    Then all data should be preserved
    And pixels should match exactly
    And frame durations should match exactly

  Scenario: Validate JSON schema
    Given I have pattern JSON data
    When I validate against schema v1.0
    Then validation should pass if JSON is valid
    And validation should fail with error if JSON is invalid

  Scenario: Migrate legacy format
    Given I have legacy pattern format without schema_version
    When I migrate to schema v1.0
    Then migrated JSON should have schema_version "1.0"
    And migrated JSON should validate against schema v1.0
    And all data should be preserved

