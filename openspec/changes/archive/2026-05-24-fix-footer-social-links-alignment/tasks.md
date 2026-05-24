## 1. Implementation
- [x] 1.1 Move social-links `<div>` into the same flex container as legal links in `templates/base.html` footer
- [x] 1.2 Simplify left side to just the copyright `<span>` (no wrapper)
- [x] 1.3 Verify mobile `< sm` vertical stacking is preserved

## 2. Validation
- [x] 2.1 Run `python manage.py runserver` and visually confirm footer layout at 320 px and 1280 px
- [x] 2.2 Use Playwright CLI to capture screenshots at 1280×800 and confirm the Instagram icon's bounding box is right of the horizontal midpoint
