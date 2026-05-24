## 1. Implementation
- [x] 1.1 Add attribution `<p>` line after the copyright `<span>` inside the left wrapper in `templates/base.html` footer, using `text-xs text-gray-400` with the anchor pointing to the WhatsApp URL
- [x] 1.2 Verify the footer layout at desktop (`sm+`) and mobile (`< sm`) is preserved (attribution wraps with copyright, no horizontal overflow)

## 2. Validation
- [x] 2.1 Open https://fastjob.localhost/ and visually confirm the attribution text renders beneath the copyright at 320 px and 1280 px (browser DevTools responsive mode)
- [x] 2.2 Confirm the link opens the WhatsApp URL in a new tab with `rel="noopener"`
