## Why

The legal pages of the platform (`/privacidad/`, `/terminos/`, `/privacy/`, `/terms/`) must be updated to fully align with the legal texts provided by the compliance consultant (excluding the consultant header metadata). Currently, several required clauses regarding user consent, data retention, detailed AEPD cookie definitions, and Instagram page disclosures are missing or simplified in the last iteration of `templates/legal/terms.html`.

## What Changes

The template [terms.html](file:///develop/django/fastjob/templates/legal/terms.html) will be updated to include the following exact texts, categorized by section:

### 1. Section 1 (Información General del Titular)
Add the following text warning users to abstain from using the site if they do not accept the terms:
> *"En caso de que no acepte los términos y condiciones que a continuación se presentan le rogamos se abstenga de utilizar el Sitio Web, reservándose la Sociedad el derecho a restringir el acceso al Sitio Web a aquellos usuarios que no los respeten."*

### 2. Section 5 (Datos Personales y Advertencia de Seguridad)
Insert the following specific clauses:
* **Voluntariness and authorization:**
  > *"El Usuario que libre, afirmativa y voluntariamente comunique a la Sociedad sus datos personales a través de los procedimientos establecidos en este Sitio Web, autoriza expresamente a la empresa a su tratamiento con la finalidad señalada, respetando la legislación vigente en cada momento en materia de datos de carácter personal y servicios de la sociedad de la información."*
* **Consequence of non-authorization:**
  > *"El Usuario que no autorice el tratamiento de sus datos, no recibirá comunicación alguna por parte de la empresa, eliminándose de inmediato las comunicaciones recibidas por el mismo calificándolas como comunicaciones erróneamente recibidas."*
* **GDPR information expansion:**
  > *"Asimismo, podrá dirigirse a dicho mail para solicitar ampliar información sobre los mismos."* (relative to `dpo@basquekide.es`)
* **Storage in automated databases:**
  > *"Los datos personales contenidos en el Sitio Web pueden ser almacenados en bases de datos automatizadas, sin serles aplicadas decisiones automatizadas, cuya titularidad corresponde en exclusiva a la empresa, asumiendo ésta todas las medidas de índole técnica, organizativa y de seguridad que garantizan la confidencialidad, integridad y calidad de la información contenida en las mismas de acuerdo con lo establecido en el Reglamento General de Protección de Datos 2016/679, de 27 de abril, sus Directrices relacionadas y la Ley Orgánica 3/2018 de 6 de diciembre."*
* **Purpose limitation:**
  > *"Los datos de carácter personal que sean comunicados voluntariamente por el Usuario se destinarán únicamente a la finalidad concreta para la que fueron recabados y de las que expresamente se informa al Usuario en el momento de su recogida en la presente Política de Privacidad."*

### 3. Section 7 (Política de Cookies - Uso de Cookies)
Add the following properties to the bullet list:
* **Anonymous browser association:**
  > *"Las "cookies" se asocian únicamente con el navegador de un ordenador determinado (un usuario anónimo)."*
* **User recognition:**
  > *"Gracias a las "cookies", resulta posible que reconozcamos los navegadores de los usuarios registrados después de que éstos se hayan autenticado por primera vez, sin que tengan que registrarse en cada visita para acceder a las áreas y servicios reservados exclusivamente a ellos."*
* **Cross-provider reading exclusion:**
  > *"Las "cookies" utilizadas no pueden leer los archivos "cookies" creados por otros proveedores."*
* **Browser warning config:**
  > *"El usuario tiene la posibilidad de configurar su navegador para que le avise por pantalla de la recepción de "cookies" o para impedir la instalación de "cookies" en su disco duro. Por favor, consulte las instrucciones y manuales de su navegador para ampliar esta información."*

### 4. Section 7 (Política de Cookies - Clasificación de las Cookies)
Update the classification heading to match:
> *"2. Según su finalidad (Clasificación de la AEPD):"*

Update the definitions with the full AEPD text:
* **Cookies de terceras partes:**
  > *"Cookies de terceras partes: Las instala en su ordenador una tercera empresa y su finalidad, entre otras, es conocer datos útiles para mejorar nuestro Sitio Web. Algunos datos recogidos son, por ejemplo: el número de visitas recibidas, el origen de las visitas, las palabras clave utilizadas para encontrarnos, o las horas de mayor afluencia de visitantes. Podrá configurar su navegador para no recibir estas "cookies" y no se instalarán."*
* **Cookies técnicas:**
  > *"Cookies técnicas: Son aquellas que permiten al usuario la navegación a través de una página web, plataforma o aplicación y la utilización de las diferentes opciones o servicios que en ella existan, incluyendo aquellas que el editor utiliza para permitir la gestión y operativa de la página web y habilitar sus funciones y servicios. (Ej.: controlar el tráfico, identificar la sesión, realizar compras, gestionar pagos, controlar el fraude, etc.). Están exceptuadas del cumplimiento de las obligaciones establecidas en el artículo 22.2 de la LSSI cuando permitan prestar el servicio solicitado por el usuario."*
* **Cookies de personalización de interfaz:**
  > *"Cookies de personalización de interfaz: Permiten recordar información para que el usuario acceda al servicio con determinadas características que pueden diferenciar su experiencia (idioma, número de resultados, región, etc.). Si el propio usuario elige esas características, estarán exceptuadas de las obligaciones del artículo 22.2 de la LSSI."*
* **Cookies de análisis o medición:**
  > *"Cookies de análisis o medición: Permiten al Responsable de las mismas el seguimiento y análisis del comportamiento de los usuarios de los sitios web, incluida la cuantificación de los impactos de los anuncios, con el fin de introducir mejoras."*
* **Cookies de publicidad comportamental:**
  > *"Cookies de publicidad comportamental: Almacenan información del comportamiento de los usuarios obtenida a través de la observación continuada de sus hábitos de navegación, lo que permite desarrollar un perfil específico para mostrar publicidad en función del mismo."*
* **Cookies de sesión:**
  > *"Cookies de sesión: Diseñadas para recabar y almacenar datos mientras el usuario accede a una página web. Se emplean para almacenar información que solo interesa conservar para la prestación del servicio solicitado en una sola ocasión y desaparecen al terminar la sesión."*

### 5. Section 7 (Política de Cookies - Cómo eliminar las cookies)
Add the following introductory text and reference to AEPD guides, and align the anchor texts:
* **Browser elimination intro:**
  > *"Desde su equipo puede eliminar las "cookies" instaladas en cada navegador que use. Al instalarse de forma individual en cada navegador, deberá eliminarlas de cada uno de ellos."*
* **AEPD guides link:**
  > *"Para más información, puede revisar las guías de la Agencia Española de Protección de Datos."*
* **Link Anchor Texts:**
  * `Eliminar "cookies" en Chrome`
  * `Eliminar "cookies" en Firefox`
  * `Eliminar "cookies" en Internet Explorer`
  * `Eliminar "cookies" en Safari`
  * `Eliminar "cookies" en Opera`

### 6. Section 7 (Política de Cookies - Consentimiento y Banner)
Incorporate the detailed layers of cookie banner information:
* **Primera capa de información:**
  > *"Primera capa de información: Al comenzar la navegación, un banner (ej. modelo Cookiebot) debe informar de la tipología de las cookies y dar opción a aceptar todas, denegar todas, ajustarlas o ampliar información."*
* **Denegación por defecto:**
  > *"Denegación por defecto: Todas las tipologías de cookies, menos las necesarias, deben aparecer por defecto como "denegadas". Si el Usuario cierra el banner sin elegir ninguna modalidad, se entenderá que sólo permite las estrictamente necesarias."*
* **Segunda capa de información:**
  > *"Segunda capa de información: Si el usuario desea configurar las cookies por tipología, se le debe mostrar un panel detallado."*
* **Tercera capa de información:**
  > *"Tercera capa de información: Opción (no habitual pero potencialmente obligatoria en el futuro) donde el Usuario pueda elegir de forma individual, cookie a cookie."*
* **Reseteo de permisos:**
  > *"Reseteo de permisos: Es recomendable resetear los permisos periódicamente. Se aconseja que este período no supere los 90 días."*

### 7. Section 8 (Política de Privacidad de Redes Sociales)
Update the heading / owner introductory lines to include the CIF and full address context:
> * **Titular:** FERNANDO PEÑA TORRE (79050303Q)
> * **Domicilio:** C\ ALMAGRO 11, 28010 MADRID (MADRID)
> * Mention of **LSSI-CE** in the introductory compliance paragraph.

Add the explicit profile consent text:
> *"El usuario, al consentir el tratamiento de sus datos, incluye explícitamente aquellos datos personales publicados en su perfil."*

### 8. Section 9 (Normativa Legal y Jurisdicción)
Inject the updateability, publication, and acceptance clauses:
* **Updateability and compliance:**
  > *"El presente “Aviso Legal”, así como el resto del contenido de este Sitio Web, se han realizado respetando en todo momento la legislación que le resulta aplicable, en especial, la referente a la Protección de Datos de carácter personal y la Ley 34/2002, de 11 de julio, de Servicios de la Sociedad de la Información y comercio electrónico, y podrán ser revisados y modificados en cualquier momento al objeto de adaptarse a cualquier modificación de la legislación vigente."*
* **Publication applicability:**
  > *"En dicho caso, el nuevo contenido resultará aplicable desde el momento en que su modificación sea publicitada en el Sitio Web, resultando accesible para los Usuarios de este."*
* **Explicit acceptance:**
  > *"El uso del Sitio Web, incluyendo el acceso por los Usuarios y la navegación a través del mismo, es libre pero implica la aceptación expresa y cumplimiento del “Aviso Legal” de este Sitio Web y de la legislación española aplicable."*

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `legal`: The requirements for Aviso Legal, Cookie Policy, and Social Media Privacy inside the legal pages are updated to include specific compliance clauses.

## Impact

- `templates/legal/terms.html`: Template layout will be updated to include all missing legal blocks.
- `templates/legal/privacy.html`: Remains unchanged as its tables and clauses are already compliant.
- `apps/core/tests/test_views.py` and other legal page tests: Test assertions will be updated to verify the presence of key new legal text blocks.
