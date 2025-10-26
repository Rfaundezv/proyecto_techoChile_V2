from core.models import Region
from proyectos.models import Proyecto, Vivienda
from django.db.models import Count

r = Region.objects.filter(nombre__icontains='valparaiso').first()
print('--- Detalle Región ---')
if not r:
    print('Región Valparaíso no encontrada')
else:
    print('Región: {} (id={})'.format(r.nombre, r.id))
    total = Vivienda.objects.filter(proyecto__region=r).count()
    entregadas = Vivienda.objects.filter(proyecto__region=r, estado='entregada').count()
    print('Total viviendas: {}'.format(total))
    print('Entregadas: {}'.format(entregadas))
    print('\nProyectos en la región:')
    qs = Proyecto.objects.filter(region=r).annotate(viv_count=Count('viviendas'))
    for p in qs:
        constructora = p.constructora.nombre if getattr(p, 'constructora', None) else (p.constructora_legacy or '—')
        comuna = p.comuna.nombre if getattr(p, 'comuna', None) else '—'
        print('- {} | {} | Viviendas: {} | Comuna: {} | Constructora: {} | Entrega: {}'.format(p.codigo, p.nombre, p.viv_count, comuna, constructora, p.fecha_entrega))
    print('\nComunas con viviendas y totales:')
    com_qs = Vivienda.objects.filter(proyecto__region=r).values('proyecto__comuna__nombre').annotate(total=Count('id')).order_by('-total')
    for c in com_qs:
        print('- {}: {}'.format(c['proyecto__comuna__nombre'], c['total']))
