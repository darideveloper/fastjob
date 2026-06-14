## MODIFIED Requirements

### Requirement: Public Terms of Service Page
The application SHALL provide a public Terms of Service page accessible at both `/terminos/` and `/terms/`. This page MUST define the legal agreement between the user and the service.

The content MUST include:
- **Aviso Legal (General Info)**: Fernando Peña Torre identity, CIF, registration, address, and the domain `www.fastjob.es`. Condition of access, and definition of "Usuario". It MUST include the warning:
  > *"En caso de que no acepte los términos y condiciones que a continuación se presentan le rogamos se abstenga de utilizar el Sitio Web, reservándose la Sociedad el derecho a restringir el acceso al Sitio Web a aquellos usuarios que no los respeten."*
- **Platform Definition**: FastJob is an automation tool, not a recruiter/employer, and guarantees no job interviews/offers.
- **Envíos Credits**: Definition of "Envíos" as consumable units that expire upon use and are non-refundable.
- **Third-Party Providers**: Delegated OAuth permissions and disclaimer of liability for account suspensions by Google/Microsoft.
- **Unsecured Channel Warning & Data Protection**: Disclaimer that communication channels are not encrypted, warning against sending sensitive/protected data. It MUST include specific data protection clauses:
  * **Voluntariness:** *"El Usuario que libre, afirmativa y voluntariamente comunique a la Sociedad sus datos personales a través de los procedimientos establecidos en este Sitio Web, autoriza expresamente a la empresa a su tratamiento con la finalidad señalada, respetando la legislación vigente en cada momento en materia de datos de carácter personal y servicios de la sociedad de la información."*
  * **Non-authorization consequence:** *"El Usuario que no autorice el tratamiento de sus datos, no recibirá comunicación alguna por parte de la empresa, eliminándose de inmediato las comunicaciones recibidas por el mismo calificándolas como comunicaciones erróneamente recibidas."*
  * **Information expansion:** *"Asimismo, podrá dirigirse a dicho mail para solicitar ampliar información sobre los mismos."*
  * **Automated storage:** *"Los datos personales contenidos en el Sitio Web pueden ser almacenados en bases de datos automatizadas, sin serles aplicadas decisiones automatizadas, cuya titularidad corresponde en exclusiva a la empresa, asumiendo ésta todas las medidas de índole técnica, organizativa y de seguridad que garantizan la confidencialidad, integridad y calidad de la información contenida en las mismas de acuerdo con lo establecido en el Reglamento General de Protección de Datos 2016/679, de 27 de abril, sus Directrices relacionadas y la Ley Orgánica 3/2018 de 6 de diciembre."*
  * **Purpose limitation:** *"Los datos de carácter personal que sean comunicados voluntariamente por el Usuario se destinarán únicamente a la finalidad concreta para la que fueron recabados y de las que expresamente se informa al Usuario en el momento de su recogida en la presente Política de Privacidad."*
- **Cookie Policy**:
  - Detailed classifications heading MUST match: `2. Según su finalidad (Clasificación de la AEPD):`
  - Detailed classifications (source, purpose, persistence) with full AEPD descriptions:
    * **Third-party:** *"Cookies de terceras partes: Las instala en su ordenador una tercera empresa y su finalidad, entre otras, es conocer datos útiles para mejorar nuestro Sitio Web. Algunos datos recogidos son, por ejemplo: el número de visitas recibidas, el origen de las visitas, las palabras clave utilizadas para encontrarnos, o las horas de mayor afluencia de visitantes. Podrá configurar su navegador para no recibir estas "cookies" y no se instalarán."*
    * **Technical:** *"Cookies técnicas: Son aquellas que permiten al usuario la navegación a través de una página web, plataforma o aplicación y la utilización de las diferentes opciones o servicios que en ella existan, incluyendo aquellas que el editor utiliza para permitir la gestión y operativa de la página web y habilitar sus funciones y servicios. (Ej.: controlar el tráfico, identificar la sesión, realizar compras, gestionar pagos, controlar el fraude, etc.). Están exceptuadas del cumplimiento de las obligaciones establecidas en el artículo 22.2 de la LSSI cuando permitan prestar el servicio solicitado por el usuario."*
    * **Personalization:** *"Cookies de personalización de interfaz: Permiten recordar información para que el usuario acceda al servicio con determinadas características que pueden diferenciar su experiencia (idioma, número de resultados, región, etc.). Si el propio usuario elige esas características, estarán exceptuadas de las obligaciones del artículo 22.2 de la LSSI."*
    * **Measurement:** *"Cookies de análisis o medición: Permiten al Responsable de las mismas el seguimiento y análisis del comportamiento de los usuarios de los sitios web, incluida la cuantificación de los impactos de los anuncios, con el fin de introducir mejoras."*
    * **Behavioral advertising:** *"Cookies de publicidad comportamental: Almacenan información del comportamiento de los usuarios obtenida a través de la observación continuada de sus hábitos de navegación, lo que permite desarrollar un perfil específico para mostrar publicidad en función del mismo."*
    * **Session:** *"Cookies de sesión: Diseñadas para recabar y almacenar datos mientras el usuario accede a una página web. Se emplean para almacenar información que solo interesa conservar para la prestación del servicio solicitado en una sola ocasión y desaparecen al terminar la sesión."*
  - It MUST include browser removal links with explicit anchor texts matching the target document:
    * `Eliminar "cookies" en Chrome`
    * `Eliminar "cookies" en Firefox`
    * `Eliminar "cookies" en Internet Explorer`
    * `Eliminar "cookies" en Safari`
    * `Eliminar "cookies" en Opera`
  - It MUST include introductory text regarding individual browser cookie deletion (*"Desde su equipo puede eliminar las "cookies" instaladas..."*), AEPD guidance link (*"Para más información, puede revisar las guías..."*), and Cookie banner requirements (including First, Second, Third layer definitions, default denial, and 90-day reset).
- **Social Media (Instagram)**:
  - Heading / owner introductory lines MUST include:
    * **Titular:** FERNANDO PEÑA TORRE (79050303Q)
    * **Domicilio:** C\ ALMAGRO 11, 28010 MADRID (MADRID)
    * Mention of **LSSI-CE** in the compliance intro.
  - User responsibility and explicit profile data consent clause:
    > *"El usuario, al consentir el tratamiento de sus datos, incluye explícitamente aquellos datos personales publicados en su perfil."*
- **Linking Policy**: External links liability disclaimer.
- **Applicable Spanish Legislation**: LSSI-CE 34/2002 (including the updateability/modification clauses) and LOPDGDD 3/2018.
- **Contacto y Soporte**: Link to `www.basquekide.es` and `dpo@basquekide.es` at the bottom of the page.

#### Scenario: User views the Terms of Service via Spanish URL
- **WHEN** they navigate to `/terminos/`
- **THEN** the page displays the terms of service covering service rules, cookie policy, social media privacy, and liability.

#### Scenario: User views the Terms of Service via English URL
- **WHEN** they navigate to `/terms/`
- **THEN** the page displays the same terms of service covering service rules, cookie policy, social media privacy, and liability.
