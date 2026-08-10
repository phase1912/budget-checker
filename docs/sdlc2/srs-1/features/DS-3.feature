Feature: Router mounts Landing at root path

  Scenario: The root path renders the Landing page
    Given a visitor requests the root path "/"
    When the router resolves the request
    Then the Landing page's content renders inside the shared Layout
