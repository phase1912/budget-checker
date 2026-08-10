Feature: Header exposes theme toggle

  Scenario: The toggle is visible in the header
    Given a visitor loads any route
    When the header renders
    Then a theme toggle control is visible in the header

  Scenario: The toggle remains present regardless of active theme
    Given the application is showing the dark theme
    When the header renders
    Then the theme toggle control is still visible in the header
