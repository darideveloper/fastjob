## Why

The marketing and informational copy on the landing page needs to be updated to better communicate the product's value proposition, improve clarity, and align with new messaging goals regarding how CVs are sent and managed.

## What Changes

Update the following 11 copy items on the landing page (`templates/home.html`) and package cards (`templates/payments/_package_card.html`):

1. **Hero Headline**:
   - *From*: "Envía tu CV a cientos de empresas de forma automática y sin spam"
   - *To*: "Envía tu CV a cientos de empresas de forma automática"
2. **Hero Subtitle**:
   - *From*: "FastJob usa tu propia cuenta de Gmail o Outlook para enviar tu CV en PDF adjunto, con alta tasa de entrega y plantillas variadas."
   - *To*: "Elige dónde y en qué quieres trabajar, sube tu CV en PDF y nosotros hacemos el resto: enviamos tu candidatura de forma automática, personalizada y segura desde tu propia cuenta de Gmail u Outlook"
3. **"How it Works" Step 2**:
   - *From*: "Sube tu CV en PDF una sola vez. Selecciona el sector y la ubicación que te interesen."
   - *To*: "Sube tu CV en PDF y dinos dónde y en qué tipo de empresas quieres trabajar"
4. **"How it Works" Step 4**:
   - *From*: "Activa tu campaña y nuestro motor enviará tu CV automáticamente, respetando los tiempos anti-spam."
   - *To*: "Activa tu campaña y deja que nuestro motor se encargue de llevar tu CV a empresas que encajan con lo que estás buscando, de forma profesional y segura"
5. **Trust Section Header**:
   - *From*: "Diseñado para máxima entregabilidad"
   - *To*: "Pensado para que tu candidatura llegue más lejos"
6. **Trust Section Card 1 (CV PDF)**:
   - *From*: "Tu CV se envía como archivo PDF adjunto, en un formato profesional y fácil de revisar por las empresas."
   - *To*: "Tu CV viaja como adjunto profesional, listo para que el reclutador lo abra al instante." (Note: This is already implemented in `templates/home.html` and requires no action, but is noted here for copy completeness).
7. **Trust Section Card 2 Title**:
   - *From*: "Slow-Drip"
   - *To*: "Envíos progresivos"
8. **Trust Section Card 2 Description**:
   - *From*: "Un email cada 5 minutos desde tu propia cuenta. Nada sospechoso."
   - *To*: "Los correos se envían de forma gradual desde tu propia cuenta, para mantener un proceso ordenado y natural."
9. **Trust Section Card 3 Title**:
   - *From*: "Plantillas variadas"
   - *To*: "Mensajes personalizados"
10. **Trust Section Card 3 Description**:
    - *From*: "Asunto y cuerpo aleatorios en cada envío para evitar patrones detectables."
    - *To*: "Cada candidatura utiliza asuntos y textos adaptados para que el contacto con las empresas sea más profesional y cercano."
11. **Package Card Feature**:
    - *From*: "Anti-spam Slow-Drip incluido"
    - *To*: "Contacto directo con empresas desde tu propia cuenta de correo" (This will update all package cards dynamically via the shared template `templates/payments/_package_card.html`).

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `landing`: Modify scenarios in the existing landing spec that reference old landing page copy assertions.

## Impact

- **UI Templates**: 
  - `templates/home.html` (Landing page)
  - `templates/payments/_package_card.html` (Package pricing cards)
