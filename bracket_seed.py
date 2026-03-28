"""
MMBP 2026 Full Bracket Seed
----------------------------
Run this once to populate the entire bracket structure into the database.
Wires up all bracket links so winners auto-advance through every round.

Usage:
    python bracket_seed.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
import models
import bracket_engine as be

models.Base.metadata.create_all(bind=engine)

# ── Bracket Data ──────────────────────────────────────────────────────────────
# Each entry: (bracket_position, player_a, seed_a, player_b, seed_b)
# bracket_position pairs: 1&2 winners meet, 3&4 winners meet, etc.
# Play-in games are round 0. Round of 64 is round 1.
# For play-in slots in R64, player name is "TBD" and seed is the higher seed.

# LEFT SIDE of bracket
# Region L-Top (positions 1-8 in R64)
LEFT_TOP_R64 = [
    # pos, playerA,         seedA, playerB,           seedB
    (1,  "Sam A",            1,   "TBD-PlayIn-1",     16),  # winner of play-in fills slot B
    (2,  "Adam K",           8,   "TBD-PlayIn-2",       9),  # A=Adam K direct, B=Alaina P/Ananya D winner
    (3,  "TBD-PlayIn-4",     5,   "TBD-PlayIn-5",     12),  # A=Ryan H/Solomon G winner, B=Adi V/Christian D winner
    (4,  "Connor R",         4,   "TBD-PlayIn-12",    13),  # B=Catherine S/David P winner
    (5,  "Kurt S",           6,   "Eric D",           11),
    (6,  "Andrew J",         3,   "Sophia R",         14),
    (7,  "Jackie L",         7,   "Lucas K",          10),
    (8,  "Morgan J",         2,   "Jacob N",          15),
]

# LEFT BOTTOM (positions 9-16 in R64)
LEFT_BOT_R64 = [
    (9,  "Matthew S",        1,   "TBD-PlayIn-6",     16),
    (10, "Ollie M",          8,   "TBD-PlayIn-7",      9),
    (11, "Jack S",           5,   "TBD-PlayIn-8",     12),
    (12, "Atai T",           4,   "Izzy N",           13),
    (13, "Kenji T",          6,   "TBD-PlayIn-9",     11),
    (14, "Gaven W",          3,   "Matt Y",           14),
    (15, "Zoe K",            7,   "Isabelle G",       10),
    (16, "Greg",             2,   "TBD-PlayIn-19",    15),  # B=Lily F/Kara M winner
]

# RIGHT TOP (positions 17-24 in R64)
RIGHT_TOP_R64 = [
    (17, "Arizona/Saaketh N",  1,  "TBD-PlayIn-10",   16),
    (18, "Villanova/Nate M",   8,  "TBD-PlayIn-11",    9),
    (19, "Wisconsin/Ryan P",   5,  "High Point/Christian B", 12),
    (20, "TBD-PlayIn-20",      4,  "Jack F",          13),  # A=Joaquin/Kora M winner, B=Jack F direct entry
    (21, "TBD-PlayIn-13",     6,  "TBD-PlayIn-14",   11),  # A=Veyd P/Casey R winner, B=Kavon C/Austin C winner
    (22, "Gonzaga/Iniyaa M",   3,  "Kennesaw St/Alexa L", 14),
    (23, "Miami/Josh W",       7,  "TBD-PlayIn-15",   10),  # B=Tanay P/Cameron W winner
    (24, "Purdue/Ryan J",      2,  "Queens/Aidan J",  15),
]

# RIGHT BOTTOM (positions 25-32 in R64)
RIGHT_BOT_R64 = [
    (25, "Michigan/Haley F",   1,  "Howard/Allison F", 16),
    (26, "Georgia/Jon O",      8,  "Saint Louis/Nico F", 9),
    (27, "Texas Tech/Violet M", 5, "Akron/Sara C",    12),
    (28, "TBD-PlayIn-18",      4,  "TBD-PlayIn-16",   13),  # A=William M/Kat M winner, B=Alex M/Ryan W winner
    (29, "Tennessee/Elise K",  6,  "TBD-PlayIn-17",   11),
    (30, "Virginia/Chloe B",   3,  "Wright St/Thomas C", 14),
    (31, "Kentucky/Orit S",    7,  "Santa Clara/York B", 10),
    (32, "Iowa St/Lyndon G",   2,  "Tennessee St/Thomas D", 15),
]

# ── Play-In Games (Round 0) ───────────────────────────────────────────────────
# (play_in_id_label, playerA, seedA, playerB, seedB, feeds_into_r64_pos, feeds_into_slot)
PLAY_INS = [
    # Left side
    ("PI-1",  "Ayat K",     16, "Alani T",      16,  1, "B"),   # → R64 pos 1 slot B (vs Sam A)
    ("PI-2",  "Alaina P",    8, "Ananya D",       9,  2, "B"),   # → R64 pos 2 slot B (vs Adam K)
    ("PI-4",  "Ryan H",      5, "Solomon G",     12,  3, "A"),   # → R64 pos 3 slot A (Ryan H / Solomon G play-in)
    ("PI-5",  "Adi V",      12, "Christian D",   13,  3, "B"),   # → R64 pos 3 slot B (vs Ryan H/Solomon G winner)
    ("PI-6",  "Stefan L",   16, "Eva A",         16,  9, "B"),   # → R64 pos 9 slot B
    ("PI-7",  "Vishakha J",  8, "Nick D",         9, 10, "B"),   # → R64 pos 10 slot B
    ("PI-8",  "Henry L",    12, "Condredge C",   12, 11, "B"),   # → R64 pos 11 slot B
    ("PI-9",  "Rishi T",     6, "Maya D",        11, 13, "B"),   # → R64 pos 13 slot B
    # Right side
    ("PI-10", "Lysol D",    16, "Lexi O",        16, 17, "B"),   # → R64 pos 17 slot B
    ("PI-11", "Ryan M",      8, "Emma H",         9, 18, "B"),   # → R64 pos 18 slot B
    ("PI-12", "Catherine S", 13, "David P",      13,  4, "B"),   # → R64 pos 4 slot B (vs Connor R)
    ("PI-13", "Veyd P",      6, "Casey R",        6, 21, "A"),   # → R64 pos 21 slot A (BYU side)
    ("PI-14", "Kavon C",    11, "Austin C",      11, 21, "B"),   # → R64 pos 21 slot B
    ("PI-15", "Tanay P",    10, "Cameron W",     10, 23, "B"),   # → R64 pos 23 slot B
    ("PI-16", "Alex M",     13, "Ryan W",         13, 28, "B"),   # → R64 pos 28 slot B
    ("PI-17", "Lok H",      11, "Jess T",        11, 29, "B"),   # → R64 pos 29 slot B
    ("PI-18", "William M",  4,  "Kat M",          4,  28, "A"),   # → R64 pos 28 slot A
    ("PI-19", "Lily F",    15,  "Kara M",        15,  16, "B"),   # → R64 pos 16 slot B
    ("PI-20", "Joaquin",    4,  "Kora M",         4,  20, "A"),   # → R64 pos 20 slot A
]


def seed_bracket(db, tournament_id: int, sport: str = "MMBP 2026"):
    print(f"Seeding bracket for tournament {tournament_id}...")

    # Step 1: Create all R64 matchups (round 1), status=pending until play-ins resolve
    r64_map = {}  # position -> matchup object
    all_r64 = LEFT_TOP_R64 + LEFT_BOT_R64 + RIGHT_TOP_R64 + RIGHT_BOT_R64

    print("Creating Round of 64 matchups...")
    for (pos, pa, sa, pb, sb) in all_r64:
        # Open immediately if both players are known (no play-in feeding this slot)
        no_playin_positions = {5, 6, 7, 8, 12, 14, 15, 19, 22, 24, 25, 26, 27, 30, 31, 32}  # pos 3,4 removed — both have play-ins
        initial_status = "open" if pos in no_playin_positions else "pending"
        odds_a, odds_b = be.get_seed_odds(sa, sb)
        m = models.Matchup(
            player_a=pa, player_b=pb,
            seed_a=sa, seed_b=sb,
            sport=sport,
            odds_a=odds_a, odds_b=odds_b,
            initial_odds_a=odds_a, initial_odds_b=odds_b,
            status=initial_status,
            tournament_id=tournament_id,
            round_number=1,
            bracket_position=pos,
        )
        db.add(m)
        db.flush()  # get id without committing
        r64_map[pos] = m
        print(f"  R64 pos {pos}: {pa} vs {pb}")

    db.commit()

    # Step 2: Create play-in matchups (round 0) and link them to R64 slots
    print("\nCreating Play-In matchups and linking...")
    play_in_map = {}
    for (label, pa, sa, pb, sb, r64_pos, slot) in PLAY_INS:
        odds_a, odds_b = be.get_seed_odds(sa, sb)
        m = models.Matchup(
            player_a=pa, player_b=pb,
            seed_a=sa, seed_b=sb,
            sport=sport,
            odds_a=odds_a, odds_b=odds_b,
            initial_odds_a=odds_a, initial_odds_b=odds_b,
            status="open",
            tournament_id=tournament_id,
            round_number=0,
            bracket_position=0,
            next_matchup_id=r64_map[r64_pos].id,
            next_slot=slot,
        )
        db.add(m)
        play_in_map[label] = m
        print(f"  {label}: {pa} vs {pb} → R64 pos {r64_pos} slot {slot}")

    db.commit()

    # Step 3: Wire up R64 → R32 bracket tree
    # R32 has 16 matchups. Winners of R64 pos pairs:
    # (1,2)→R32-1, (3,4)→R32-2, (5,6)→R32-3, (7,8)→R32-4
    # (9,10)→R32-5, (11,12)→R32-6, (13,14)→R32-7, (15,16)→R32-8
    # (17,18)→R32-9, (19,20)→R32-10, (21,22)→R32-11, (23,24)→R32-12
    # (25,26)→R32-13, (27,28)→R32-14, (29,30)→R32-15, (31,32)→R32-16
    print("\nCreating Round of 32 matchups...")
    r64_pairs = [
        (1,2),(3,4),(5,6),(7,8),
        (9,10),(11,12),(13,14),(15,16),
        (17,18),(19,20),(21,22),(23,24),
        (25,26),(27,28),(29,30),(31,32),
    ]
    r32_map = {}
    for i, (posA, posB) in enumerate(r64_pairs, 1):
        m = models.Matchup(
            player_a=f"TBD (R64-{posA} winner)",
            player_b=f"TBD (R64-{posB} winner)",
            seed_a=None, seed_b=None,
            sport=sport,
            odds_a=2.0, odds_b=2.0,
            status="pending",
            tournament_id=tournament_id,
            round_number=2,
            bracket_position=i,
        )
        db.add(m)
        db.flush()
        r32_map[i] = m
        print(f"  R32 pos {i}: R64-{posA} winner vs R64-{posB} winner")

        # Link R64 matchups to this R32 slot
        r64_map[posA].next_matchup_id = m.id
        r64_map[posA].next_slot = "A"
        r64_map[posB].next_matchup_id = m.id
        r64_map[posB].next_slot = "B"

    db.commit()

    # Step 4: Wire R32 → Sweet 16 (8 matchups)
    print("\nCreating Sweet 16 matchups...")
    r32_pairs = [(1,2),(3,4),(5,6),(7,8),(9,10),(11,12),(13,14),(15,16)]
    s16_map = {}
    for i, (posA, posB) in enumerate(r32_pairs, 1):
        m = models.Matchup(
            player_a=f"TBD (R32-{posA} winner)",
            player_b=f"TBD (R32-{posB} winner)",
            seed_a=None, seed_b=None,
            sport=sport,
            odds_a=2.0, odds_b=2.0,
            status="pending",
            tournament_id=tournament_id,
            round_number=3,
            bracket_position=i,
        )
        db.add(m)
        db.flush()
        s16_map[i] = m
        print(f"  S16 pos {i}: R32-{posA} winner vs R32-{posB} winner")

        r32_map[posA].next_matchup_id = m.id
        r32_map[posA].next_slot = "A"
        r32_map[posB].next_matchup_id = m.id
        r32_map[posB].next_slot = "B"

    db.commit()

    # Step 5: Wire S16 → Elite 8 (4 matchups)
    print("\nCreating Elite 8 matchups...")
    s16_pairs = [(1,2),(3,4),(5,6),(7,8)]
    e8_map = {}
    for i, (posA, posB) in enumerate(s16_pairs, 1):
        m = models.Matchup(
            player_a=f"TBD (S16-{posA} winner)",
            player_b=f"TBD (S16-{posB} winner)",
            seed_a=None, seed_b=None,
            sport=sport,
            odds_a=2.0, odds_b=2.0,
            status="pending",
            tournament_id=tournament_id,
            round_number=4,
            bracket_position=i,
        )
        db.add(m)
        db.flush()
        e8_map[i] = m
        print(f"  E8 pos {i}: S16-{posA} winner vs S16-{posB} winner")

        s16_map[posA].next_matchup_id = m.id
        s16_map[posA].next_slot = "A"
        s16_map[posB].next_matchup_id = m.id
        s16_map[posB].next_slot = "B"

    db.commit()

    # Step 6: Wire E8 → Final Four (2 matchups)
    print("\nCreating Final Four matchups...")
    e8_pairs = [(1,2),(3,4)]
    f4_map = {}
    for i, (posA, posB) in enumerate(e8_pairs, 1):
        m = models.Matchup(
            player_a=f"TBD (E8-{posA} winner)",
            player_b=f"TBD (E8-{posB} winner)",
            seed_a=None, seed_b=None,
            sport=sport,
            odds_a=2.0, odds_b=2.0,
            status="pending",
            tournament_id=tournament_id,
            round_number=5,
            bracket_position=i,
        )
        db.add(m)
        db.flush()
        f4_map[i] = m
        print(f"  F4 pos {i}: E8-{posA} winner vs E8-{posB} winner")

        e8_map[posA].next_matchup_id = m.id
        e8_map[posA].next_slot = "A"
        e8_map[posB].next_matchup_id = m.id
        e8_map[posB].next_slot = "B"

    db.commit()

    # Step 7: Wire F4 → Championship (1 matchup)
    print("\nCreating Championship matchup...")
    champ = models.Matchup(
        player_a="TBD (F4-1 winner)",
        player_b="TBD (F4-2 winner)",
        seed_a=None, seed_b=None,
        sport=sport,
        odds_a=2.0, odds_b=2.0,
        status="pending",
        tournament_id=tournament_id,
        round_number=6,
        bracket_position=1,
    )
    db.add(champ)
    db.flush()

    f4_map[1].next_matchup_id = champ.id
    f4_map[1].next_slot = "A"
    f4_map[2].next_matchup_id = champ.id
    f4_map[2].next_slot = "B"

    db.commit()
    print(f"\n✅ Bracket seeded successfully!")
    print(f"   Play-In games: {len(PLAY_INS)}")
    print(f"   Round of 64:   {len(all_r64)}")
    print(f"   Round of 32:   {len(r32_map)}")
    print(f"   Sweet 16:      {len(s16_map)}")
    print(f"   Elite 8:       {len(e8_map)}")
    print(f"   Final Four:    {len(f4_map)}")
    print(f"   Championship:  1")
    print(f"\n   Total matchups created: {len(PLAY_INS) + len(all_r64) + len(r32_map) + len(s16_map) + len(e8_map) + len(f4_map) + 1}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        # Check if tournament already exists
        tournaments = db.query(models.Tournament).all()
        if tournaments:
            print("Existing tournaments:")
            for t in tournaments:
                print(f"  [{t.id}] {t.name} (round {t.current_round})")
            tid = input("\nEnter tournament ID to seed into (or press Enter to create new): ").strip()
            if tid:
                tournament_id = int(tid)
            else:
                name = input("New tournament name [MMBP 2026]: ").strip() or "MMBP 2026"
                t = models.Tournament(name=name, current_round=0, status="active")
                db.add(t)
                db.commit()
                tournament_id = t.id
                print(f"Created tournament ID {tournament_id}")
        else:
            name = input("Tournament name [MMBP 2026]: ").strip() or "MMBP 2026"
            t = models.Tournament(name=name, current_round=0, status="active")
            db.add(t)
            db.commit()
            tournament_id = t.id
            print(f"Created tournament ID {tournament_id}")

        confirm = input(f"\nThis will seed the FULL bracket into tournament {tournament_id}. Continue? (y/n): ")
        if confirm.lower() == 'y':
            seed_bracket(db, tournament_id)
        else:
            print("Aborted.")
    finally:
        db.close()
