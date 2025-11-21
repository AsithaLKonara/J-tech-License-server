Feature: Drawing Tools
  As a designer
  I want to use drawing tools to create LED patterns
  So that I can design animations efficiently

  Background:
    Given I have opened the Design Tools tab
    And I have created a new 16x16 pattern
    And I have selected frame 0

  Scenario: Draw with Pixel tool
    Given I have selected the Pixel tool
    When I click at position (5, 5) with color (255, 0, 0)
    Then pixel at (5, 5) should be (255, 0, 0)

  Scenario: Draw rectangle
    Given I have selected the Rectangle tool
    When I drag from (2, 2) to (8, 8) with color (0, 255, 0)
    Then rectangle from (2, 2) to (8, 8) should be filled with (0, 255, 0)

  Scenario: Draw circle
    Given I have selected the Circle tool
    When I drag from (8, 8) to (12, 12) with color (0, 0, 255)
    Then circle with center (10, 10) and radius 4 should be drawn with (0, 0, 255)

  Scenario: Draw line
    Given I have selected the Line tool
    When I drag from (0, 0) to (15, 15) with color (255, 255, 0)
    Then line from (0, 0) to (15, 15) should be drawn with (255, 255, 0)

  Scenario: Fill area
    Given I have selected the Fill tool
    When I click at position (8, 8) with color (255, 0, 255)
    Then all connected pixels starting from (8, 8) should be filled with (255, 0, 255)

