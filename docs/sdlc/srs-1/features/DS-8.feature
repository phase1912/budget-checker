Feature: Default to light theme

  Scenario: No stored preference and no OS preference, so light is applied
    Given no theme preference is stored
    And the operating system reports no color-scheme preference
    When the application loads
    Then the light theme is applied
