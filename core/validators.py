import re
from django.core.exceptions import ValidationError

RUT_REGEX = re.compile(r'^\d{1,8}-[0-9kK]$')

def clean_rut(value: str) -> str:
    # Normalizar: quitar puntos y espacios
    v = str(value).replace('.', '').replace(' ', '').upper()
    if '-' not in v and len(v) > 1:
        v = v[:-1] + '-' + v[-1]
    return v


def validar_rut(value: str):
    if not value:
        return
    v = clean_rut(value)
    if not RUT_REGEX.match(v):
        raise ValidationError('RUT con formato inválido')

    num, dv = v.split('-')
    try:
        num = int(num)
    except ValueError:
        raise ValidationError('RUT inválido')
    # calcular dígito verificador usando el algoritmo módulo 11
    s = 0
    multiplier = 2
    for digit in reversed(str(num)):
        s += int(digit) * multiplier
        multiplier += 1
        if multiplier > 7:
            multiplier = 2
    remainder = s % 11
    dv_calc_num = 11 - remainder
    if dv_calc_num == 11:
        dv_calc = '0'
    elif dv_calc_num == 10:
        dv_calc = 'K'
    else:
        dv_calc = str(dv_calc_num)

    if dv_calc != dv.upper():
        raise ValidationError('Dígito verificador inválido')
