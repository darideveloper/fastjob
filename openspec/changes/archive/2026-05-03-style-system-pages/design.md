# Design: System Page Styling

## Architectural Reasoning
FastJob uses a server-side rendering (SSR) approach with Django Templates and Tailwind CSS. The current `base.html` includes a Tailwind CDN script and an inline configuration. To satisfy the requirement of "easy to edit colors and fonts in a single place," we will:

1.  **Centralize Tailwind Config**: Refine the `tailwind.config` block in `base.html` to include a custom theme with semantic names (e.g., `brand-primary`, `brand-accent`).
2.  **Standardize Component Layouts**: Use a consistent container structure across all system pages (centered card on a light gray background), matching the existing `login.html` aesthetic.

## Component Strategy

### Template Inheritance
All new templates MUST start with `{% extends "base.html" %}`.

### Card Layout Component
To avoid duplication across `logout.html`, `signup.html`, etc., we will define a common "Auth/System Card" structure:
```html
<div class="max-w-md mx-auto px-4 py-16">
  <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
    <!-- Page specific content -->
  </div>
</div>
```

## Theme Configuration
The `base.html` will be updated to:
```javascript
tailwind.config = {
  theme: {
    extend: {
      colors: {
        brand: { 
          DEFAULT: '#4F46E5', // Indigo 600
          light: '#6366F1',   // Indigo 500
          dark: '#3730A3'     // Indigo 800
        },
        surface: '#F9FAFB',   // Gray 50
        accent: '#4F46E5'     // Semantic alias for brand
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
      }
    }
  }
}
```

## Affected Files
- `templates/base.html` (Centralized config)
- `templates/account/logout.html` (New)
- `templates/socialaccount/signup.html` (New)
- `templates/socialaccount/authentication_error.html` (New)
- `templates/socialaccount/login_cancelled.html` (New)
- `templates/socialaccount/connections.html` (New)
- `templates/404.html` (New)
- `templates/500.html` (New)
