from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    balance = Column(Float, default=1000.0)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bets = relationship("Bet", back_populates="user")


class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    current_round = Column(Integer, default=0)
    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    matchups = relationship("Matchup", back_populates="tournament")


class Matchup(Base):
    __tablename__ = "matchups"

    id = Column(Integer, primary_key=True, index=True)
    player_a = Column(String, nullable=False)
    player_b = Column(String, nullable=False)
    seed_a = Column(Integer, nullable=True)
    seed_b = Column(Integer, nullable=True)
    sport = Column(String, default="Sport")
    odds_a = Column(Float, default=2.0)
    odds_b = Column(Float, default=2.0)
    initial_odds_a = Column(Float, default=2.0)  # original seed odds, never changes
    initial_odds_b = Column(Float, default=2.0)
    status = Column(String, default="open")
    winner = Column(String, nullable=True)
    winner_name = Column(String, nullable=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=True)
    round_number = Column(Integer, nullable=True)
    bracket_position = Column(Integer, nullable=True)
    next_matchup_id = Column(Integer, ForeignKey("matchups.id"), nullable=True)
    next_slot = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tournament = relationship("Tournament", back_populates="matchups")
    bets = relationship("Bet", back_populates="matchup")


class Bet(Base):
    __tablename__ = "bets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    matchup_id = Column(Integer, ForeignKey("matchups.id"), nullable=False)
    pick = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    odds_at_bet = Column(Float, nullable=False)
    potential_payout = Column(Float, nullable=False)
    settled = Column(Boolean, default=False)
    won = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="bets")
    matchup = relationship("Matchup", back_populates="bets")
