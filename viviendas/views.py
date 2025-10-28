from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.decorators import rol_requerido
from proyectos.models import Vivienda

@login_required
@rol_requerido('ADMINISTRADOR', 'TECHO')
def lista_viviendas(request):
    viviendas = Vivienda.objects.filter(activa=True).select_related('proyecto')
    total_viviendas = viviendas.count()
    context = {
        'viviendas': viviendas,
        'total_viviendas': total_viviendas,
    }
    return render(request, 'viviendas/lista.html', context)
