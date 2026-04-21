from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    location: Mapped[str] = mapped_column(String(150), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="scheduled")
    draw_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    players: Mapped[list["Player"]] = relationship(back_populates="tournament", cascade="all, delete-orphan")
    matches: Mapped[list["Match"]] = relationship(back_populates="tournament", cascade="all, delete-orphan")


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (UniqueConstraint("tournament_id", "name", name="uq_player_name_per_tournament"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    tournament: Mapped[Tournament] = relationship(back_populates="players")


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    round_name: Mapped[str] = mapped_column(String(50), nullable=False)
    table_no: Mapped[str] = mapped_column(String(20), nullable=False)
    player_a: Mapped[str] = mapped_column(String(120), nullable=False)
    player_b: Mapped[str] = mapped_column(String(120), nullable=False)
    score_a: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score_b: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_finished: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    tournament: Mapped[Tournament] = relationship(back_populates="matches")
