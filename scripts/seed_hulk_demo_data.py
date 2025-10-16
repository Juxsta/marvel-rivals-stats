#!/usr/bin/env python3
"""Seed database with comprehensive sample data focused on Hulk analysis.

This script creates realistic sample data to demonstrate the character
analysis and synergy features, with a focus on Hulk (Vanguard).
"""

import os
import random
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.connection import get_connection


def generate_sample_data():
    """Generate comprehensive sample data for demo."""
    # Sample players with various ranks
    players = [
        ("HulkSmash247", "Diamond", 4850),
        ("GreenMachine", "Platinum", 4200),
        ("BruceMain", "Diamond", 4920),
        ("TankMaster", "Platinum", 4350),
        ("LunaHealer99", "Diamond", 4780),
        ("SpideySwing", "Gold", 3900),
        ("IronDPS", "Platinum", 4400),
        ("StrangeSupport", "Gold", 3700),
        ("VenomSniper", "Diamond", 4650),
        ("BlackCatNinja", "Platinum", 4250),
        ("ThorHammer", "Gold", 3850),
        ("CapShield", "Diamond", 4800),
        ("WidowShot", "Platinum", 4150),
        ("HawkeyeAim", "Gold", 3950),
        ("ScarletMain", "Diamond", 4700),
        ("MantisZen", "Platinum", 4300),
        ("GrootSupport", "Gold", 3800),
        ("RocketGun", "Diamond", 4600),
        ("StarLordBlast", "Platinum", 4100),
        ("MagnetoMaster", "Gold", 3750),
    ]

    # Hero pool with realistic IDs
    heroes = {
        # Vanguards
        "Hulk": (1003, "vanguard"),
        "Captain America": (1004, "vanguard"),
        "Thor": (1020, "vanguard"),
        "Groot": (1009, "vanguard"),
        "Magneto": (1014, "vanguard"),
        # Duelists
        "Spider-Man": (1001, "duelist"),
        "Iron Man": (1002, "duelist"),
        "Black Widow": (1003, "duelist"),
        "Venom": (1022, "duelist"),
        "Scarlet Witch": (1007, "duelist"),
        "Hawkeye": (1007, "duelist"),
        "Star-Lord": (1011, "duelist"),
        # Strategists
        "Luna Snow": (1013, "strategist"),
        "Doctor Strange": (1008, "strategist"),
        "Mantis": (1012, "strategist"),
        "Rocket Raccoon": (1010, "strategist"),
    }

    # Generate matches with Hulk having good synergy with Luna Snow and Doctor Strange
    matches = []
    participants = []

    base_time = datetime.now() - timedelta(days=7)
    match_count = 150  # Generate 150 matches

    for i in range(match_count):
        match_id = f"match_{i:04d}"
        match_time = base_time + timedelta(hours=i)
        matches.append((match_id, "competitive", 1, match_time))

        # Randomly select 12 players for this match (6v6)
        match_players = random.sample(players, min(12, len(players)))

        # Determine teams and winner
        team0_won = random.choice([True, False])

        # Assign heroes to players
        for player_idx, (username, rank_tier, rank_score) in enumerate(match_players):
            team = player_idx % 2  # Alternate teams
            won = (team == 0 and team0_won) or (team == 1 and not team0_won)

            # Special logic: If player is a Hulk main, use Hulk
            if "Hulk" in username or "Green" in username or "Bruce" in username:
                hero_name = "Hulk"

                # Hulk has better win rate with Luna Snow and Doctor Strange
                if i % 3 == 0:  # Every 3rd match, pair with Luna Snow
                    teammate_hero = "Luna Snow"
                elif i % 5 == 0:  # Every 5th match, pair with Doctor Strange
                    teammate_hero = "Doctor Strange"
                else:
                    teammate_hero = None

                # Add Hulk's synergy partner to the same team
                if teammate_hero and player_idx + 1 < len(match_players):
                    synergy_player = match_players[player_idx + 1]
                    hero_id, role = heroes[teammate_hero]
                    participants.append(
                        (
                            match_id,
                            synergy_player[0],  # username
                            hero_id,
                            teammate_hero,
                            role,
                            team,
                            won,
                            random.randint(1, 5),  # kills
                            random.randint(1, 3),  # deaths
                            random.randint(10, 25),  # assists
                            random.randint(5000, 12000),  # damage
                            random.randint(20000, 40000),  # healing
                        )
                    )
            elif "Luna" in username:
                hero_name = "Luna Snow"
            elif "Strange" in username or "Support" in username:
                hero_name = "Doctor Strange"
            elif "Spid" in username:
                hero_name = "Spider-Man"
            elif "Iron" in username:
                hero_name = "Iron Man"
            elif "Thor" in username:
                hero_name = "Thor"
            elif "Cap" in username:
                hero_name = "Captain America"
            elif "Widow" in username:
                hero_name = "Black Widow"
            elif "Venom" in username:
                hero_name = "Venom"
            elif "Scarlet" in username:
                hero_name = "Scarlet Witch"
            elif "Mantis" in username:
                hero_name = "Mantis"
            elif "Groot" in username:
                hero_name = "Groot"
            elif "Rocket" in username:
                hero_name = "Rocket Raccoon"
            elif "Star" in username:
                hero_name = "Star-Lord"
            elif "Hawk" in username:
                hero_name = "Hawkeye"
            elif "Magneto" in username:
                hero_name = "Magneto"
            else:
                # Random hero
                hero_name = random.choice(list(heroes.keys()))

            hero_id, role = heroes[hero_name]

            # Generate realistic stats based on role
            if role == "vanguard":
                kills = random.randint(4, 12)
                deaths = random.randint(2, 8)
                assists = random.randint(8, 20)
                damage = random.randint(12000, 25000)
                healing = 0
            elif role == "duelist":
                kills = random.randint(10, 20)
                deaths = random.randint(3, 10)
                assists = random.randint(4, 12)
                damage = random.randint(20000, 35000)
                healing = 0
            else:  # strategist
                kills = random.randint(1, 6)
                deaths = random.randint(1, 5)
                assists = random.randint(12, 25)
                damage = random.randint(5000, 15000)
                healing = random.randint(20000, 40000)

            participants.append(
                (
                    match_id,
                    username,
                    hero_id,
                    hero_name,
                    role,
                    team,
                    won,
                    kills,
                    deaths,
                    assists,
                    damage,
                    healing,
                )
            )

    return players, matches, participants


def main():
    """Seed the database with sample data."""
    print("=" * 60)
    print("Seeding Hulk Demo Data")
    print("=" * 60)
    print()

    # Generate data
    print("Generating sample data...")
    players, matches, participants = generate_sample_data()
    print(f"✓ Generated {len(players)} players")
    print(f"✓ Generated {len(matches)} matches")
    print(f"✓ Generated {len(participants)} match participants")
    print()

    # Connect to database
    try:
        conn = get_connection()
        cur = conn.cursor()
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        sys.exit(1)

    try:
        # Insert players
        print("Inserting players...")
        for username, rank_tier, rank_score in players:
            cur.execute(
                """
                INSERT INTO players (
                    username, rank_tier, rank_score, discovered_at, match_history_fetched
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (username) DO UPDATE
                SET rank_tier = EXCLUDED.rank_tier,
                    rank_score = EXCLUDED.rank_score
            """,
                (username, rank_tier, rank_score, datetime.now(), True),
            )
        print(f"✓ Inserted {len(players)} players")

        # Insert matches
        print("Inserting matches...")
        for match_id, mode, season, match_timestamp in matches:
            cur.execute(
                """
                INSERT INTO matches (match_id, mode, season, match_timestamp)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (match_id) DO NOTHING
            """,
                (match_id, mode, season, match_timestamp),
            )
        print(f"✓ Inserted {len(matches)} matches")

        # Insert match participants
        print("Inserting match participants...")
        for participant_data in participants:
            cur.execute(
                """
                INSERT INTO match_participants (
                    match_id, username, hero_id, hero_name, role, team,
                    won, kills, deaths, assists, damage, healing
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (match_id, username) DO NOTHING
            """,
                participant_data,
            )
        print(f"✓ Inserted {len(participants)} match participants")

        conn.commit()

        # Verify data
        print()
        print("-" * 60)
        print("Verifying inserted data...")
        print("-" * 60)

        cur.execute("SELECT COUNT(*) FROM players")
        player_count = cur.fetchone()[0]
        print(f"Total players: {player_count}")

        cur.execute("SELECT COUNT(*) FROM matches")
        match_count = cur.fetchone()[0]
        print(f"Total matches: {match_count}")

        cur.execute("SELECT COUNT(*) FROM match_participants")
        participant_count = cur.fetchone()[0]
        print(f"Total match participants: {participant_count}")

        # Check Hulk stats
        cur.execute(
            """
            SELECT COUNT(*) FROM match_participants
            WHERE hero_name = 'Hulk'
        """
        )
        hulk_games = cur.fetchone()[0]
        print(f"Hulk games: {hulk_games}")

        print()
        print("✓ Sample data seeded successfully!")
        print()

    except Exception as e:
        conn.rollback()
        print(f"✗ Failed to seed data: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
