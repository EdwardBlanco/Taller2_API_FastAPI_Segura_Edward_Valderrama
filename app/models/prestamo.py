from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base

if TYPE_CHECKING:
    from .libro import Libro
    from .socio import Socio
    from .usuario import Usuario


class Prestamo(Base):
    __tablename__ = "prestamos"

    id: Mapped[int] = mapped_column(primary_key=True)
    libro_id: Mapped[int] = mapped_column(ForeignKey("libros.id"), nullable=False)
    socio_id: Mapped[int] = mapped_column(ForeignKey("socios.id"), nullable=False)
    fecha_prestamo: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    fecha_limite: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_devolucion: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    multa: Mapped[float] = mapped_column(Numeric(10, 2, asdecimal=False), default=0.0, nullable=False)
    multa_pagada: Mapped[bool] = mapped_column(default=False, nullable=False)
    registrado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)

    libro: Mapped["Libro"] = relationship(back_populates="prestamos", lazy="selectin")
    socio: Mapped["Socio"] = relationship(back_populates="prestamos", lazy="selectin")
    registrado_por: Mapped["Usuario | None"] = relationship(lazy="selectin")

    @property
    def estado(self) -> str:
        if self.fecha_devolucion is not None:
            return "devuelto"
        if self.fecha_limite < date.today():
            return "vencido"
        return "activo"
