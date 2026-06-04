from django.db import migrations

def seed_faqs(apps, schema_editor):
    FAQ = apps.get_model('core', 'FAQ')
    faqs = [
        {
            "question": "¿Qué es FastJob?",
            "answer": "FastJob es una plataforma que automatiza el envío de tu currículum a empresas que encajan con tu perfil profesional. Tú subes tu CV, seleccionas tus preferencias y nosotros nos encargamos del resto.",
            "order": 1
        },
        {
            "question": "¿Cómo funciona?",
            "answer": "Solo tienes que conectar tu cuenta de correo electrónico, subir tu currículum y seleccionar tus preferencias laborales. FastJob identifica empresas relevantes y envía automáticamente tus candidaturas.",
            "order": 2
        },
        {
            "question": "¿Los correos se envían desde mi cuenta?",
            "answer": "Sí. Todas las candidaturas se envían desde tu propia dirección de correo electrónico. Las empresas pueden responderte directamente y los mensajes aparecen en tu bandeja de enviados.",
            "order": 3
        },
        {
            "question": "¿Las empresas reciben realmente mi CV?",
            "answer": "Sí. Tu currículum se adjunta en cada candidatura y se envía directamente a los contactos profesionales de las empresas seleccionadas.",
            "order": 4
        },
        {
            "question": "¿Qué ocurre si un correo rebota y no llega al destinatario?",
            "answer": "Algunas empresas pueden haber cambiado sus direcciones de contacto o tener configuraciones que impidan la recepción de determinados correos. Por ello, FastJob envía aproximadamente un 30&nbsp;% más de candidaturas sin coste adicional para compensar posibles rebotes y maximizar el número de envíos efectivos.<br/><br/>Por ejemplo:<br/><ul class=\"list-disc pl-5 mt-2 space-y-1\"><li>Plan 50&nbsp;envíos → aproximadamente 65&nbsp;envíos.</li><li>Plan 200&nbsp;envíos → aproximadamente 260&nbsp;envíos.</li><li>Plan 600&nbsp;envíos → aproximadamente 780&nbsp;envíos.</li></ul>",
            "order": 5
        },
        {
            "question": "¿Necesito buscar ofertas de empleo?",
            "answer": "No. FastJob te ayuda a contactar directamente con empresas que podrían necesitar perfiles como el tuyo, incluso aunque no tengan una vacante publicada en ese momento.",
            "order": 6
        },
        {
            "question": "¿Mis datos y mi correo están seguros?",
            "answer": "Sí. FastJob no almacena tu contraseña ni tiene acceso directo a tus credenciales. La conexión con Gmail y Outlook se realiza mediante sistemas seguros de autorización proporcionados por los propios proveedores.",
            "order": 7
        },
        {
            "question": "¿Puedo retirar el acceso a mi correo cuando quiera?",
            "answer": "Sí. Puedes revocar el acceso de FastJob a tu cuenta en cualquier momento desde la configuración de seguridad de Gmail o Outlook.",
            "order": 8
        },
        {
            "question": "¿Quién puede utilizar FastJob?",
            "answer": "Cualquier persona que esté buscando empleo o nuevas oportunidades profesionales: estudiantes, recién graduados, profesionales con experiencia o personas que actualmente ya estén trabajando.",
            "order": 9
        },
        {
            "question": "¿Cómo seleccionáis las empresas a las que se envía mi CV?",
            "answer": "Las empresas se seleccionan en función de los criterios que indiques, como sector, ubicación, área profesional o tamaño de empresa, buscando siempre la máxima relevancia para tu perfil.",
            "order": 10
        },
        {
            "question": "¿Podré ver las candidaturas enviadas?",
            "answer": "Sí. Como los correos se envían desde tu propia cuenta, podrás revisar todos los envíos directamente desde tu bandeja de salida.",
            "order": 11
        },
        {
            "question": "¿Qué ocurre si una empresa me responde?",
            "answer": "La respuesta llegará directamente a tu correo electrónico para que puedas continuar la conversación sin intermediarios.",
            "order": 12
        },
        {
            "question": "¿FastJob garantiza que conseguiré trabajo?",
            "answer": "No. Ninguna plataforma puede garantizar una contratación. Lo que sí hacemos es multiplicar el alcance de tu búsqueda y aumentar significativamente el número de empresas que reciben tu candidatura.",
            "order": 13
        },
        {
            "question": "¿Por qué utilizar FastJob en lugar de enviar CVs manualmente?",
            "answer": "Porque te permite ahorrar horas de trabajo repetitivo, llegar a muchas más empresas y centrarte en lo importante: preparar entrevistas y encontrar la oportunidad adecuada.",
            "order": 14
        }
    ]
    for faq_data in faqs:
        FAQ.objects.create(**faq_data)

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0003_initial'),
    ]
    operations = [
        migrations.RunPython(seed_faqs),
    ]
