Feature: Landing page redesign

  Scenario: The landing page shows styled content
    Given a visitor opens the landing page
    When the page renders
    Then the heading, body text, and status line are styled with the theme's typography, color, and spacing
    And no element renders with unstyled default browser presentation
