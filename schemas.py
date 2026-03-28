from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    balance: float
    is_admin: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    is_admin: bool


# ── Tournament ────────────────────────────────────────────────────────────────

class TournamentCreate(BaseModel):
    name: str


class TournamentOut(BaseModel):
    id: int
    name: str
    current_round: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Matchups ──────────────────────────────────────────────────────────────────

class MatchupCreate(BaseModel):
    player_a: str
    player_b: str
    seed_a: Optional[int] = None
    seed_b: Optional[int] = None
    sport: str = "Sport"
    odds_a: float = Field(default=2.0, gt=1.0)
    odds_b: float = Field(default=2.0, gt=1.0)
    tournament_id: Optional[int] = None
    round_number: Optional[int] = None
    bracket_position: Optional[int] = None


class MatchupOut(BaseModel):
    id: int
    player_a: str
    player_b: str
    seed_a: Optional[int]
    seed_b: Optional[int]
    sport: str
    odds_a: float
    odds_b: float
    status: str
    winner: Optional[str]
    winner_name: Optional[str]
    tournament_id: Optional[int]
    round_number: Optional[int]
    bracket_position: Optional[int]
    next_matchup_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class MatchupResult(BaseModel):
    winner: str  # "A" or "B"


class OddsUpdate(BaseModel):
    odds_a: float = Field(gt=1.0)
    odds_b: float = Field(gt=1.0)


# ── Tournament Matchup Setup ──────────────────────────────────────────────────

class TournamentMatchupEntry(BaseModel):
    player_a: str
    player_b: str
    seed_a: Optional[int] = None
    seed_b: Optional[int] = None
    bracket_position: int


class TournamentSetup(BaseModel):
    tournament_id: int
    round_number: int
    sport: str = "MMBP 2026"
    matchups: List[TournamentMatchupEntry]


# ── Bets ──────────────────────────────────────────────────────────────────────

class BetCreate(BaseModel):
    matchup_id: int
    pick: str
    amount: float = Field(gt=0)


class BetOut(BaseModel):
    id: int
    matchup_id: int
    pick: str
    amount: float
    odds_at_bet: float
    potential_payout: float
    settled: bool
    won: Optional[bool]
    created_at: datetime

    class Config:
        from_attributes = True


class BetWithUser(BaseModel):
    id: int
    matchup_id: int
    username: str
    pick: str
    amount: float
    odds_at_bet: float
    potential_payout: float
    settled: bool
    won: Optional[bool]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Leaderboard ───────────────────────────────────────────────────────────────

class LeaderboardEntry(BaseModel):
    username: str
    balance: float
    total_bets: int
    total_won: int
