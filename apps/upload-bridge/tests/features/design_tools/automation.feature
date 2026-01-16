Feature: Automation Actions
  As a designer
  I want to apply automation actions to patterns
  So that I can create complex animations

  Background:
    Given I have opened the Design Tools tab
    And I have created a new 16x16 pattern with 10 frames

  Scenario: Apply scroll effect
    Given I have selected frames 0-9
    When I apply scroll action with direction "right" and speed 1.0
    Then pixels should scroll right across frames
    And transformation should be deterministic

  Scenario: Apply rotate effect
    Given I have selected frames 0-9
    When I apply rotate action
    Then pixels should rotate 90 degrees clockwise
    And transformation should be deterministic

  Scenario: Apply mirror effect
    Given I have selected frames 0-9
    When I apply mirror action with axis "horizontal"
    Then pixels should be mirrored horizontally
    And transformation should be deterministic

  Scenario: Apply wipe effect
    Given I have selected frames 0-9
    When I apply wipe action with direction "right" and color (255, 0, 0)
    Then frames should wipe from left to right with red color
    And progression should be smooth across frames

  Scenario: Apply bounce effect
    Given I have selected frames 0-9
    When I apply bounce action with direction "vertical"
    Then pixels should bounce vertically
    And animation should oscillate smoothly

