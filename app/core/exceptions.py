class ErrorAplicacion(Exception):
    codigo: int = 400

    def __init__(self, mensaje: str = "Error en la aplicación"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class NoEncontrado(ErrorAplicacion):
    codigo: int = 404

    def __init__(self, mensaje: str = "El recurso no existe"):
        super().__init__(mensaje)


class Conflicto(ErrorAplicacion):
    codigo: int = 409

    def __init__(self, mensaje: str = "Conflicto con el recurso"):
        super().__init__(mensaje)


class ReglaNegocio(ErrorAplicacion):
    codigo: int = 422

    def __init__(self, mensaje: str = "Regla de negocio no cumplida"):
        super().__init__(mensaje)


class NoAutenticado(ErrorAplicacion):
    codigo: int = 401

    def __init__(self, mensaje: str = "Credenciales inválidas"):
        super().__init__(mensaje)


class Prohibido(ErrorAplicacion):
    codigo: int = 403

    def __init__(self, mensaje: str = "No tiene permisos para esta acción"):
        super().__init__(mensaje)


class CuentaBloqueada(ErrorAplicacion):
    codigo: int = 423

    def __init__(self, mensaje: str = "Cuenta bloqueada temporalmente"):
        super().__init__(mensaje)
