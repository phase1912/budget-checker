Feature: Fallback to OS theme preference

  Scenario Outline: No stored preference exists, so the OS preference is applied
    Given no theme preference is stored
    And the operating system reports a <preference> preference
    When the application loads
    Then the <preference> theme is applied

    Examples:
      | preference |
      | light      |
      | dark       |

  Scenario: localStorage is unavailable, so the OS preference is used instead
    Given localStorage is unavailable in the visitor's browser
    And the operating system reports a light-mode preference
    When the application loads
    Then the light theme is applied
