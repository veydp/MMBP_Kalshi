from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class MatchupStatus(str, enum.Enum):
    open = "open"
    closed = "closed"
    settled = "settled"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    balance = Column(Float, default=1000.0)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bets = relationship("Bet", back_populates="user")


class Matchup(Base):
    __tablename__ = "matchups"

    id = Column(Integer, primary_key=True, index=True)
    player_a = Column(String, nullable=False)
    player_b = Column(String, nullable=False)
    sport = Column(String, default="Sport")
    odds_a = Column(Float, default=2.0)   # decimal odds for player A
    odds_b = Column(Float, default=2.0)   # decimal odds for player B
    status = Column(String, default="open")  # open | closed | settled
    winner = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bets = relationship("Bet", back_populates="matchup")


class Bet(Base):
    __tablename__ = "bets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    matchup_id = Column(Integer, ForeignKey("matchups.id"), nullable=False)
    pick = Column(String, nullable=False)   # "A" or "B"
    amount = Column(Float, nullable=False)
    odds_at_bet = Column(Float, nullable=False)
    potential_payout = Column(Float, nullable=False)
    settled = Column(Boolean, default=False)
    won = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="bets")
    matchup = relationship("Matchup", back_populates="bets")
