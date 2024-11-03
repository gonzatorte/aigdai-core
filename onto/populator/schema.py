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

repositorio_m2m_organizacion = Table(
    "repositorio_m2m_organizacion",
    Base.metadata,
    Column("organizacion_id", ForeignKey("organizacion.id"), primary_key=True),
    Column("repositorio_id", ForeignKey("repositorio.id"), primary_key=True),
)

repositorio_m2m_certificacion = Table(
    "repositorio_m2m_certificacion",
    Base.metadata,
    Column("certificacion_id", ForeignKey("certificacion.id"), primary_key=True),
    Column("repositorio_id", ForeignKey("repositorio.id"), primary_key=True),
)

repositorio_m2m_pidesquema = Table(
    "repositorio_m2m_pidesquema",
    Base.metadata,
    Column("pidesquema_id", ForeignKey("pidesquema.id"), primary_key=True),
    Column("repositorio_id", ForeignKey("repositorio.id"), primary_key=True),
)

repositorio_m2m_disciplina = Table(
    "repositorio_m2m_disciplina",
    Base.metadata,
    Column("disciplina_id", ForeignKey("disciplina.id"), primary_key=True),
    Column("repositorio_id", ForeignKey("repositorio.id"), primary_key=True),
)

repositorio_m2m_api = Table(
    "repositorio_m2m_api",
    Base.metadata,
    Column("api_id", ForeignKey("api.id"), primary_key=True),
    Column("repositorio_id", ForeignKey("repositorio.id"), primary_key=True),
)

repositorio_m2m_palabraclave = Table(
    "repositorio_m2m_palabraclave",
    Base.metadata,
    Column("palabraclave_id", ForeignKey("palabraclave.id"), primary_key=True),
    Column("repositorio_id", ForeignKey("repositorio.id"), primary_key=True),
)

# ToDo: Definir el esquema de donde sale esa disciplina?
class Disciplina(Base):
    __tablename__ = "disciplina"
    id: Mapped[str] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    id_esquema: Mapped[str] = mapped_column(String(100))

    repositorios: Mapped[List["Repositorio"]] = relationship(back_populates="disciplinas", secondary=repositorio_m2m_disciplina)

    def __repr__(self) -> str:
        return f"Disciplina(id={self.id!r}, nombre={self.nombre!r})"


class PalabraClave(Base):
    __tablename__ = "palabraclave"
    id: Mapped[str] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    vocab_id: Mapped[Optional[str]] = mapped_column(ForeignKey("vocabulariocontrolado.id"))
    vocab: Mapped[Optional["VocabularioControlado"]] = relationship(back_populates="palabras_claves")

    repositorios: Mapped[List["Repositorio"]] = relationship(back_populates="palabrasclaves", secondary=repositorio_m2m_palabraclave)

    def __repr__(self) -> str:
        return f"PalabraClave(id={self.id!r}, nombre={self.nombre!r})"


class VocabularioControlado(Base):
    __tablename__ = "vocabulariocontrolado"
    id: Mapped[str] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))

    def __repr__(self) -> str:
        return f"VocabularioControlado(id={self.id!r}, nombre={self.nombre!r})"


class Certificacion(Base):
    __tablename__ = "certificacion"
    id: Mapped[str] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))

    repositorios: Mapped[List["Repositorio"]] = relationship(back_populates="certificaciones", secondary=repositorio_m2m_certificacion)

    def __repr__(self) -> str:
        return f"Certificacion(id={self.id!r}, nombre={self.nombre!r})"


class PidEsquema(Base):
    __tablename__ = "pidesquema"
    id: Mapped[str] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))

    repositorios: Mapped[List["Repositorio"]] = relationship(back_populates="pidesquemas", secondary=repositorio_m2m_pidesquema)

    def __repr__(self) -> str:
        return f"PidEsquema(id={self.id!r}, nombre={self.nombre!r})"


class Repositorio(Base):
    __tablename__ = "repositorio"
    # id: Mapped[int] = mapped_column(primary_key=True)
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(160))
    descripcion: Mapped[Optional[str]] = mapped_column(String(3000))
    sitio_web: Mapped[Optional[str]] = mapped_column(String(160))

    pidesquema: Mapped[List["PidEsquema"]] = relationship(back_populates="repositorios", secondary=repositorio_m2m_pidesquema)
    organizaciones: Mapped[List["Organizacion"]] = relationship(back_populates="repositorios", secondary=repositorio_m2m_organizacion)
    certificaciones: Mapped[List["Certificacion"]] = relationship(back_populates="repositorios", secondary=repositorio_m2m_certificacion)
    disciplinas: Mapped[List["Disciplina"]] = relationship(back_populates="repositorios", secondary=repositorio_m2m_disciplina)
    apis: Mapped[List["Api"]] = relationship(back_populates="repositorios", secondary=repositorio_m2m_api)
    palabrasclaves: Mapped[List["PalabraClave"]] = relationship(back_populates="repositorios", secondary=repositorio_m2m_palabraclave)

    motor_id: Mapped[Optional[str]] = mapped_column(ForeignKey("motor.id"))
    motor: Mapped[Optional["Motor"]] = relationship(back_populates="repositorios")

    politicas: Mapped[List["Politica"]] = relationship(back_populates="repositorios", secondary=repositorio_m2m_politica)

    def __repr__(self) -> str:
        return f"Repositorio(id={self.id!r}, nombre={self.nombre!r})"


class Organizacion(Base):
    __tablename__ = "organizacion"
    id: Mapped[str] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))

    repositorios: Mapped[List["Repositorio"]] = relationship(back_populates="organizaciones", secondary=repositorio_m2m_organizacion)

    def __repr__(self) -> str:
        return f"Organizacion(id={self.id!r}, nombre={self.nombre!r})"


class Politica(Base):
    __tablename__ = "politica"
    id: Mapped[str] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))

    repositorios: Mapped[List["Repositorio"]] = relationship(back_populates="politicas", secondary=repositorio_m2m_politica)

    def __repr__(self) -> str:
        return f"Politica(id={self.id!r}, nombre={self.nombre!r})"


class Motor(Base):
    __tablename__ = "motor"
    id: Mapped[str] = mapped_column(primary_key=True)

    repositorios: Mapped[List["Repositorio"]] = relationship(back_populates="motor")

    def __repr__(self) -> str:
        return f"Motor(id={self.id!r})"


class Api(Base):
    __tablename__ = "api"
    id: Mapped[str] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(100)) # ToDo: Enum

    repositorios: Mapped[List["Repositorio"]] = relationship(back_populates="apis", secondary=repositorio_m2m_api)

    def __repr__(self) -> str:
        return f"Api(id={self.id!r}, {self.type!r})"
