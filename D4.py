"""Gestor de la caja de un comercio para aplicación de consola.

Integra menú en bucle, selección múltiple (match/case), control de excepciones
en todas las entradas, funciones documentadas y los cuatro patrones de trabajo
sobre datos y entradas.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


FORMAS_PAGO: dict[str, str] = {
    "1": "Efectivo",
    "2": "Tarjeta",
    "3": "Bizum",
}

IMPORTE_MINIMO: float = 0.01
IMPORTE_MAXIMO: float = 100_000.0


@dataclass(frozen=True)
class Venta:
    """Representa una operación de venta registrada en la caja."""

    identificador: int
    importe: float
    forma_pago: str
    hora: str


def leer_entero(mensaje: str, minimo: int | None = None, maximo: int | None = None) -> int:
    """Solicita un número entero por consola con control de excepciones y rangos.

    Patrón 1: Lectura validada en bucle hasta obtener un entero válido.
    """
    while True:
        try:
            raw = input(mensaje).strip()
            if raw == "":
                raise ValueError("La entrada no puede estar vacía.")
            valor = int(raw)
            if minimo is not None and valor < minimo:
                print(f"Error: el valor debe ser mayor o igual que {minimo}.")
                continue
            if maximo is not None and valor > maximo:
                print(f"Error: el valor debe ser menor o igual que {maximo}.")
                continue
            return valor
        except ValueError as exc:
            print(f"Entrada no válida ({exc}). Introduce un número entero.")
        except (EOFError, KeyboardInterrupt):
            print("\nEntrada interrumpida. Inténtalo de nuevo.")


def leer_float(
    mensaje: str,
    minimo: float | None = None,
    maximo: float | None = None,
) -> float:
    """Solicita un número decimal positivo por consola con control de excepciones.

    Acepta coma o punto como separador decimal y redondea a dos decimales.
    """
    while True:
        try:
            raw = input(mensaje).strip().replace(",", ".")
            if raw == "":
                raise ValueError("El importe no puede estar vacío.")
            valor = float(raw)
            if valor != valor or valor in (float("inf"), float("-inf")):
                raise ValueError("Número no finito.")
            if minimo is not None and valor < minimo:
                print(f"Error: el importe debe ser al menos {minimo:.2f} €.")
                continue
            if maximo is not None and valor > maximo:
                print(f"Error: el importe no puede superar {maximo:.2f} €.")
                continue
            return round(valor, 2)
        except ValueError as exc:
            print(f"Importe no válido ({exc}). Ejemplo válido: 12.50 o 12,50.")
        except (EOFError, KeyboardInterrupt):
            print("\nEntrada interrumpida. Inténtalo de nuevo.")


def leer_forma_pago() -> str:
    """Solicita y valida la forma de pago mediante selección controlada."""
    while True:
        try:
            print("\nFormas de pago disponibles:")
            for clave, etiqueta in FORMAS_PAGO.items():
                print(f"  {clave}. {etiqueta}")
            opcion = input("Selecciona forma de pago (1-3): ").strip()
            if opcion not in FORMAS_PAGO:
                raise ValueError("Opción de forma de pago fuera de rango.")
            return FORMAS_PAGO[opcion]
        except ValueError as exc:
            print(f"Error: {exc}")
        except (EOFError, KeyboardInterrupt):
            print("\nEntrada interrumpida. Inténtalo de nuevo.")


def registrar_venta(ventas: list[Venta], siguiente_id: int) -> tuple[Venta, int]:
    """Registra una nueva venta en la lista activa y devuelve (venta, nuevo_id).

    Patrón 3 (parte de registro): añade la venta al final de la pila (LIFO).
    """
    importe = leer_float(
        f"Importe de la venta ({IMPORTE_MINIMO:.2f} € - {IMPORTE_MAXIMO:.2f} €): ",
        minimo=IMPORTE_MINIMO,
        maximo=IMPORTE_MAXIMO,
    )
    forma_pago = leer_forma_pago()
    hora_actual = datetime.now().strftime("%H:%M:%S")
    nueva_venta = Venta(
        identificador=siguiente_id,
        importe=importe,
        forma_pago=forma_pago,
        hora=hora_actual,
    )
    ventas.append(nueva_venta)
    return nueva_venta, siguiente_id + 1


def anular_ultima_venta(ventas: list[Venta]) -> Venta | None:
    """Elimina y devuelve la última venta registrada (LIFO), o None si está vacía.

    Patrón 3 (parte de anulación): desapila el último elemento con pop().
    """
    if not ventas:
        return None
    return ventas.pop()


def calcular_metricas(ventas: list[Venta]) -> dict[str, float | int | None]:
    """Calcula total del día, número de operaciones, importe medio y venta mayor.

    Patrón 2: Acumulador, contador y máximo sobre la secuencia de ventas.
    """
    total_dia: float = 0.0
    num_operaciones: int = 0
    venta_mayor: float | None = None

    for venta in ventas:
        total_dia = round(total_dia + venta.importe, 2)
        num_operaciones += 1
        if venta_mayor is None or venta.importe > venta_mayor:
            venta_mayor = venta.importe

    importe_medio: float = round(total_dia / num_operaciones, 2) if num_operaciones > 0 else 0.0

    return {
        "total_dia": total_dia,
        "num_operaciones": num_operaciones,
        "importe_medio": importe_medio,
        "venta_mayor": venta_mayor,
    }


def mostrar_estado_actual(ventas: list[Venta]) -> None:
    """Muestra por consola el resumen acumulado del día."""
    metricas = calcular_metricas(ventas)
    mayor_str = (
        f"{metricas['venta_mayor']:.2f} €"
        if isinstance(metricas["venta_mayor"], float)
        else "Sin ventas"
    )
    print("\n--- ESTADO ACTUAL DE CAJA ---")
    print(f"Total del día:         {metricas['total_dia']:.2f} €")
    print(f"Número de operaciones: {metricas['num_operaciones']}")
    print(f"Importe medio:         {metricas['importe_medio']:.2f} €")
    print(f"Venta mayor:           {mayor_str}")


def construir_resumen_cierre(ventas: list[Venta]) -> str:
    """Genera el texto completo del cierre de caja, incluyendo desglose por pago."""
    metricas = calcular_metricas(ventas)
    totales_por_pago: dict[str, float] = {etiqueta: 0.0 for etiqueta in FORMAS_PAGO.values()}
    conteo_por_pago: dict[str, int] = {etiqueta: 0 for etiqueta in FORMAS_PAGO.values()}

    for venta in ventas:
        totales_por_pago[venta.forma_pago] = round(
            totales_por_pago.get(venta.forma_pago, 0.0) + venta.importe, 2
        )
        conteo_por_pago[venta.forma_pago] = conteo_por_pago.get(venta.forma_pago, 0) + 1

    mayor_str = (
        f"{metricas['venta_mayor']:.2f} €"
        if isinstance(metricas["venta_mayor"], float)
        else "0.00 € (sin ventas)"
    )

    lineas = [
        "\n==========================================",
        "           RESUMEN DE CIERRE DE CAJA       ",
        "==========================================",
        f"Total del día:          {metricas['total_dia']:.2f} €",
        f"Número de operaciones:  {metricas['num_operaciones']}",
        f"Importe medio:          {metricas['importe_medio']:.2f} €",
        f"Venta mayor:            {mayor_str}",
        "------------------------------------------",
        "Desglose por forma de pago:",
    ]
    for forma, total_forma in totales_por_pago.items():
        lineas.append(f"  - {forma:<10}: {conteo_por_pago[forma]} op. | {total_forma:.2f} €")
    lineas.append("==========================================")
    return "\n".join(lineas)


def imprimir_menu() -> None:
    """Imprime las opciones disponibles del menú de caja."""
    print("\n=== GESTOR DE CAJA DEL COMERCIO ===")
    print("1. Registrar venta")
    print("2. Anular última venta")
    print("3. Consultar estado del día (total, operaciones, medio, mayor)")
    print("4. Cerrar caja y mostrar resumen")


def ejecutar_caja() -> None:
    """Ejecuta el bucle principal del gestor de caja hasta el cierre definitivo.

    Patrón 4: Bucle controlado por condición de cierre/salida.
    """
    ventas: list[Venta] = []
    siguiente_id: int = 1
    caja_cerrada: bool = False

    while not caja_cerrada:
        imprimir_menu()
        opcion = leer_entero("Elige una opción (1-4): ", minimo=1, maximo=4)

        match opcion:
            case 1:
                venta, siguiente_id = registrar_venta(ventas, siguiente_id)
                print(
                    f"Venta #{venta.identificador} registrada: "
                    f"{venta.importe:.2f} € ({venta.forma_pago}) a las {venta.hora}."
                )
            case 2:
                anulada = anular_ultima_venta(ventas)
                if anulada is None:
                    print("No hay ventas registradas para anular.")
                else:
                    print(
                        f"Anulada la venta #{anulada.identificador}: "
                        f"{anulada.importe:.2f} € ({anulada.forma_pago})."
                    )
            case 3:
                mostrar_estado_actual(ventas)
            case 4:
                print(construir_resumen_cierre(ventas))
                caja_cerrada = True
            case _:
                print("Opción no reconocida.")


if __name__ == "__main__":
    ejecutar_caja()
