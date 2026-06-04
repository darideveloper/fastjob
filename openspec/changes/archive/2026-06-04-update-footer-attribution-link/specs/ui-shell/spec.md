## MODIFIED Requirements

### Requirement: Footer attribution line
The footer in `templates/base.html` SHALL render a small attribution line immediately below the copyright text, inside the same left-aligned wrapper, reading `Powered by DariDeveloper` where `DariDeveloper` is a hyperlink.

The attribution SHALL:
- use `text-xs text-gray-400` styling (smaller and more muted than the copyright line)
- sit on its own line below the copyright `<span>` with only the natural inline gap (no extra `mt-*` or `mb-*`)
- wrap within the parent container without causing horizontal overflow on any viewport
- render the anchor `<a>` with `href="https://www.darideveloper.com/"`, `target="_blank"`, and `rel="noopener"`
- inherit the footer's `hover:text-brand transition` on the link (matching other footer links)

The existing footer layout invariant MUST be preserved: at `< sm`, the copyright + attribution stack vertically above the social and legal clusters; at `sm+`, the left group (copyright + attribution + social) sits on the left and the legal links on the right.

#### Scenario: Attribution renders below copyright on every page
- **WHEN** any page that extends `base.html` is rendered
- **THEN** the footer contains a `Powered by DariDeveloper` text node
- **AND** `DariDeveloper` is wrapped in an `<a>` with `href="https://www.darideveloper.com/"`
- **AND** that anchor carries `target="_blank"` and `rel` containing `noopener`
- **AND** the `<a>` uses `text-gray-400 hover:text-brand transition` styling
- **AND** the attribution line is below the `© … FastJob` copyright text

#### Scenario: Attribution does not break the footer layout at 320 px
- **GIVEN** an anonymous visitor at viewport 320 × 568
- **WHEN** the footer renders
- **THEN** `document.documentElement.scrollWidth === 320` (no horizontal overflow)
- **AND** the attribution text is fully visible (not clipped or overflowing its parent)

#### Scenario: Attribution does not break the footer layout at 1280 px
- **GIVEN** an anonymous visitor at viewport 1280 × 800
- **WHEN** the footer renders
- **THEN** the attribution text sits below the copyright text inside the left group
- **AND** the social-links cluster and legal-links cluster are in their correct positions (left group vs. right group per the existing layout)
