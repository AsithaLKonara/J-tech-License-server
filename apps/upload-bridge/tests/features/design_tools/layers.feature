Feature: Layer Management
  As a designer
  I want to use multiple layers per frame
  So that I can compose complex animations

  Background:
    Given I have opened the Design Tools tab
    And I have created a new 16x16 pattern
    And I have selected frame 0

  Scenario: Add layer to frame
    Given frame 0 has 1 layer
    When I add a new layer to frame 0
    Then frame 0 should have 2 layers
    And new layer should be visible and fully opaque

  Scenario: Set layer opacity
    Given frame 0 has a layer at index 0
    When I set layer opacity to 0.5
    Then layer opacity should be 0.5
    And composite pixels should reflect opacity

  Scenario: Set layer blend mode
    Given frame 0 has 2 layers
    When I set layer 1 blend mode to "add"
    Then layer 1 blend mode should be "add"
    And composite pixels should use additive blending

  Scenario: Toggle layer visibility
    Given frame 0 has 2 layers
    And layer 1 is visible
    When I toggle layer 1 visibility
    Then layer 1 should not be visible
    And composite pixels should not include layer 1

  Scenario: Reorder layers
    Given frame 0 has 3 layers: "base", "overlay", "effects"
    When I move "effects" layer above "base" layer
    Then layer order should be: "effects", "base", "overlay"
    And composite pixels should reflect new order

