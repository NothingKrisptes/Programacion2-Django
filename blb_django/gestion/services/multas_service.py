from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from ..models import Multa

@transaction.atomic
def ensure_multa_retraso(prestamo):
    """
    Crea o actualiza la multa de retraso (tipo='r') para un préstamo.
    - Si no hay retraso: no hace nada.
    - Si hay retraso y la multa no existe: la crea.
    - Si existe y NO está pagada: actualiza monto al valor actual.
    - Si está pagada: no cambia nada.
    """
    if prestamo.dias_retraso <= 0:
        return None

    multa, created = Multa.objects.get_or_create(
        prestamo=prestamo,
        tipo='r',
        defaults={
            "monto": Decimal(str(prestamo.multa_retraso)),
            "pagada": False,
            "fecha": timezone.now().date(),
        }
    )

    if not created and not multa.pagada:
        nuevo_monto = Decimal(str(prestamo.multa_retraso))
        if multa.monto != nuevo_monto:
            multa.monto = nuevo_monto
            multa.save()

    return multa
