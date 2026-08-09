Feature: Apply stored theme preference on load

  Scenario: A stored preference is applied on load
    Given the dark theme is stored as the visitor's preference
    When the application loads
    Then the dark theme is the active theme
