from django.db import migrations


def normalize_names(apps, schema_editor):
    Beneficiario = apps.get_model('proyectos', 'Beneficiario')
    for b in Beneficiario.objects.all():
        full = b.nombre.strip() if b.nombre else ''
        tokens = full.split()
        if len(tokens) >= 3:
            maternal = tokens[-1]
            paternal = tokens[-2]
            name = ' '.join(tokens[:-2])
        elif len(tokens) == 2:
            maternal = ''
            paternal = tokens[-1]
            name = tokens[0]
        elif len(tokens) == 1:
            maternal = ''
            paternal = ''
            name = tokens[0]
        else:
            maternal = ''
            paternal = ''
            name = ''
        b.nombre = name
        b.apellido_paterno = paternal
        b.apellido_materno = maternal
        b.save()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('proyectos', '0004_remove_beneficiario_telefonos_alter_beneficiario_rut_and_more'),
    ]

    operations = [
        migrations.RunPython(normalize_names, noop_reverse),
    ]
