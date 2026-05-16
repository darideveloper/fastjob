# dashboard delta

## ADDED Requirements

### Requirement: Dashboard restyle preserves existing layout and toggle pattern
`templates/dashboard/index.html` SHALL retain its current responsive structure:

- a header row containing the page title and the **campaign toggle** (the toggle stays inline in the header, not in a column),
- a stats grid of four cards (`grid sm:grid-cols-2 lg:grid-cols-4`) immediately below the header,
- a content grid `grid lg:grid-cols-3` with a left rail at `lg:col-span-1` (CV list + upload form + Filters + Danger Zone) and a right area at `lg:col-span-2` (Recent Activity table).

The rebrand is a **restyle in place**. The activity table's `min-w-[640px]` MUST be preserved so its four columns stay readable; reflowing it into a narrower column would force horizontal scroll, contradicting the `ui-shell` no-overflow invariant.

Every panel's chrome MUST migrate to the brand tokens: `border-gray-100` → `border-brand-muted`, while keeping `bg-white`, `rounded-2xl`, and `shadow-sm`. Section titles (currently `font-bold text-lg`) MUST adopt `text-h2 text-brand-dark`. The "Actualizar búsqueda" submit button (currently `bg-gray-900 hover:bg-black`) MUST be replaced with `bg-brand hover:bg-brand-dark text-white`. The stats card's primary numeric (`text-brand`) remains, now resolving to the new Vibrant Blue.

#### Scenario: Dashboard layout structure is unchanged
- **GIVEN** a logged-in user at viewport 1280 × 800
- **WHEN** they load `/dashboard/`
- **THEN** the header row contains the page title on the left and the campaign-toggle form on the right
- **AND** below the header, a 4-card stats grid renders in `lg:grid-cols-4`
- **AND** below the stats, a content grid renders with `lg:grid-cols-3`, where CVs + Filters + Danger Zone sit in `lg:col-span-1` and Recent Activity sits in `lg:col-span-2`

#### Scenario: Panel chrome migrates to brand tokens without reflow
- **WHEN** the dashboard renders post-change
- **THEN** every panel's border class resolves to `brand.muted` (not `gray-100`)
- **AND** every section title uses `text-h2` size and `brand.dark` color
- **AND** the "Actualizar búsqueda" submit button's background resolves to `brand.DEFAULT` and on hover to `brand.dark`
- **AND** the `min-w-[640px]` constraint on the recent-activity `<table>` is unchanged

### Requirement: Campaign toggle preserves semantic start/stop colors
The campaign on/off control on the dashboard SHALL retain its current **two-button pattern** in the header row (one rendered when the campaign is active, the other when it is inactive). The "Pausar campaña" button MUST keep its red treatment (`bg-red-500 hover:bg-red-600 text-white`) and the "Iniciar campaña" button MUST keep its green treatment (`bg-green-500 hover:bg-green-600 text-white`); red and green encode stop/start affordance universally and are explicitly permitted by the `ui-shell` "Centralized Brand Identity" exception for semantic status colors.

The rebrand SHALL only add brand-coherent **focus styling** to both buttons (`focus:outline-none focus:ring-2 focus:ring-brand-ring focus:ring-offset-2`) so keyboard users see the brand's focus signal. The pattern MUST NOT be replaced by a unified switch / toggle component, and the buttons MUST NOT be re-skinned in `brand.*` palette colors.

#### Scenario: Active campaign renders the red "Pausar campaña" button
- **GIVEN** a user with `is_campaign_active == True` on `/dashboard/`
- **WHEN** the page renders
- **THEN** the header right side shows a `<button>` with classes resolving to `bg-red-500` and `hover:bg-red-600`
- **AND** its label is `Pausar campaña`
- **AND** the button additionally carries `focus:ring-2 focus:ring-brand-ring focus:ring-offset-2`

#### Scenario: Inactive campaign renders the green "Iniciar campaña" button
- **GIVEN** a user with `is_campaign_active == False` and a linked provider on `/dashboard/`
- **WHEN** the page renders
- **THEN** the header right side shows a `<button>` with classes resolving to `bg-green-500` and `hover:bg-green-600`
- **AND** its label is `Iniciar campaña`
- **AND** the button additionally carries the brand focus-ring utility set

### Requirement: Unified form-control styling on dashboard inputs
Every `<input>`, `<select>`, and `<textarea>` on `templates/dashboard/index.html` and `templates/dashboard/delete_account.html` SHALL share the same visual treatment: `bg-white border border-brand-muted rounded-lg px-3 py-2 text-brand-ink focus:outline-none focus:ring-2 focus:ring-brand-ring focus:border-brand`. The combobox widgets (`data-combobox="area"` / `"location"`) MUST adopt the same focused appearance via their existing JavaScript controller (no behavior change to the controller itself).

#### Scenario: All dashboard inputs share the same focus ring
- **GIVEN** a logged-in user on `/dashboard/`
- **WHEN** they Tab through every form field, including the CV-name input, the combobox widgets, and any input on the delete-account page
- **THEN** each focused field renders an outline using `brand.ring` and a `brand.DEFAULT` border color
- **AND** no field exhibits a different focus color or border treatment
