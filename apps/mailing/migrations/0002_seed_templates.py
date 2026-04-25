from django.db import migrations


TEMPLATES = [
    {
        "name": "Directo — Profesional",
        "subject": "Candidatura para {company_name}",
        "body_html": """
<p>Estimado equipo de {company_name},</p>

<p>Me pongo en contacto con ustedes porque estoy interesado/a en formar parte de su equipo.
Considero que mi experiencia y habilidades pueden aportar valor a {company_name}.</p>

<p>Adjunto el enlace a mi currículum para su revisión:</p>
<p><a href="{cv_url}" style="display:inline-block;padding:10px 20px;background:#4F46E5;color:#fff;
text-decoration:none;border-radius:6px;">Descargar CV</a></p>

<p>Quedo a su disposición para cualquier información adicional.</p>

<p>Un cordial saludo.</p>

<hr style="margin-top:30px;border:none;border-top:1px solid #eee;">
<p style="font-size:11px;color:#999;">
Si no desea recibir más correos,
<a href="{unsubscribe_url}" style="color:#999;">haga clic aquí para cancelar la suscripción</a>.
</p>
""".strip(),
    },
    {
        "name": "Breve — Cercano",
        "subject": "¿Tienen vacantes en {company_name}?",
        "body_html": """
<p>Hola,</p>

<p>Les escribo porque sigo desde hace tiempo el trabajo de {company_name} y me encantaría
poder sumar a su equipo. Soy un profesional motivado y con ganas de aportar.</p>

<p>Les dejo por aquí mi CV por si tuvieran alguna oportunidad abierta o quisieran
tenerme en cuenta para el futuro:</p>

<p>➡ <a href="{cv_url}">Ver mi CV</a></p>

<p>Cualquier feedback es bienvenido. ¡Muchas gracias por su tiempo!</p>

<p>Saludos cordiales.</p>

<hr style="margin-top:30px;border:none;border-top:1px solid #eee;">
<p style="font-size:11px;color:#999;">
¿No le interesa? <a href="{unsubscribe_url}" style="color:#999;">Dese de baja aquí</a>.
</p>
""".strip(),
    },
    {
        "name": "Motivacional — Entusiasta",
        "subject": "Propuesta de candidatura — {company_name}",
        "body_html": """
<p>Buenos días,</p>

<p>Mi nombre aparece en el CV adjunto y escribo con la esperanza de formar parte
del equipo de <strong>{company_name}</strong>. La trayectoria de la empresa me inspira
y creo que puedo contribuir con ideas frescas y compromiso diario.</p>

<p>Aquí está mi CV:</p>
<p><a href="{cv_url}" style="color:#4F46E5;font-weight:600;">📄 Descargar currículum</a></p>

<p>Si consideran que mi perfil puede encajar en alguna posición actual o futura,
estaría encantado/a de conocer más sobre {company_name}.</p>

<p>Agradezco mucho su atención.</p>

<p>Un saludo.</p>

<hr style="margin-top:30px;border:none;border-top:1px solid #eee;">
<p style="font-size:11px;color:#999;">
Para dejar de recibir estos correos,
<a href="{unsubscribe_url}" style="color:#999;">cancele su suscripción aquí</a>.
</p>
""".strip(),
    },
]


def seed_templates(apps, schema_editor):
    EmailTemplate = apps.get_model("mailing", "EmailTemplate")
    SystemSettings = apps.get_model("mailing", "SystemSettings")

    for t in TEMPLATES:
        EmailTemplate.objects.get_or_create(
            name=t["name"],
            defaults={
                "subject": t["subject"],
                "body_html": t["body_html"],
                "is_active": True,
            },
        )

    SystemSettings.objects.get_or_create(
        pk=1,
        defaults={"global_send_interval_minutes": 5, "company_cooldown_hours": 12},
    )


def unseed_templates(apps, schema_editor):
    EmailTemplate = apps.get_model("mailing", "EmailTemplate")
    EmailTemplate.objects.filter(name__in=[t["name"] for t in TEMPLATES]).delete()


class Migration(migrations.Migration):
    dependencies = [("mailing", "0001_initial")]
    operations = [migrations.RunPython(seed_templates, unseed_templates)]
