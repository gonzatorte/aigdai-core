from typing import List, Optional
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Table, Column


class Base(DeclarativeBase):
    pass


repositorio_m2m_politica = Table(
    "repositorio_m2m_politica",
    Base.metadata,
    Column("politica_id", ForeignKey("politica.id"), primary_key=True),
    Column("repositorio_id", ForeignKey("repositorio.id"), primary_key=True),
)


class Repositorio(Base):
    __tablename__ = "repositorio"
    # id: Mapped[int] = mapped_column(primary_key=True)
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(160))
    descripcion: Mapped[Optional[str]] = mapped_column(String(3000))
    sitio_web: Mapped[Optional[str]] = mapped_column(String(160))

    organizacion_id: Mapped[Optional[str]] = mapped_column(ForeignKey("organizacion.id"))
    organizacion: Mapped[Optional["Organizacion"]] = relationship(back_populates="repositorios")

    motor_id: Mapped[Optional[str]] = mapped_column(ForeignKey("motor.id"))
    motor: Mapped[Optional["Motor"]] = relationship(back_populates="repositorios")

    politicas: Mapped[List["Politica"]] = relationship(back_populates="repositorios", secondary=repositorio_m2m_politica)

    def __repr__(self) -> str:
        return f"Repositorio(id={self.id!r}, nombre={self.nombre!r})"


class Organizacion(Base):
    __tablename__ = "organizacion"
    id: Mapped[str] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50))

    repositorios: Mapped[List["Repositorio"]] = relationship(back_populates="organizacion")

    def __repr__(self) -> str:
        return f"Organizacion(id={self.id!r}, nombre={self.nombre!r})"


class Politica(Base):
    __tablename__ = "politica"
    id: Mapped[str] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50))

    repositorios: Mapped[List["Repositorio"]] = relationship(back_populates="politicas", secondary=repositorio_m2m_politica)

    def __repr__(self) -> str:
        return f"Politica(id={self.id!r}, nombre={self.nombre!r})"


class Motor(Base):
    __tablename__ = "motor"
    id: Mapped[str] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50))

    repositorios: Mapped[List["Repositorio"]] = relationship(back_populates="motor")

    def __repr__(self) -> str:
        return f"Motor(id={self.id!r}, nombre={self.nombre!r})"
