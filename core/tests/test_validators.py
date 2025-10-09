from django.core.exceptions import ValidationError
from django.test import TestCase
from core.validators import validar_rut


class ValidarRUTTests(TestCase):
    def test_valid_ruts(self):
        valid = [
            '12.345.678-5',
            '12345678-5',
            '1-9',
            '7645123-0',
        ]
        for r in valid:
            # should not raise
            validar_rut(r)

    def test_invalid_ruts(self):
        invalid = [
            '12.345.678-0',
            'abcdef',
            '12345678',
            '12.345.678-9',
        ]
        for r in invalid:
            with self.assertRaises(ValidationError, msg=f"rut {r} should be invalid"):
                validar_rut(r)
