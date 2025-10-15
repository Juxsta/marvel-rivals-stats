#!/usr/bin/env python3
"""Seed database with sample data for testing.

This script inserts sample players, matches, and match participants
into the database for testing purposes.
"""

import os
import sys
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def main():
    """Insert sample data into the database."""
    print("=" * 60)
    print("Seeding Sample Data")
    print("=" * 60)
    print()

    try:
        database_url = os.getenv("DATABASE_URL")
        conn = psycopg2.connect(database_url)
    except psycopg2.Error as e:
        print(f"✗ Database connection failed: {e}")
        sys.exit(1)

    try:
        with conn.cursor() as cur:
            # Sample players
            print("Inserting sample players...")
            players = [
                ("SpiderGamer2024", "Diamond", 4850),
                ("IronDefender", "Platinum", 4200),
                ("StrangeSupport", "Gold", 3700),
                ("ThorMain", "Diamond", 4920),
                ("BlackWidowSniper", "Platinum", 4350),
            ]

            for username, rank_tier, rank_score in players:
                cur.execute("""
                    INSERT INTO players (username, rank_tier, rank_score, discovered_at, match_history_fetched)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (username) DO NOTHING
                """, (username, rank_tier, rank_score, datetime.now(), False))

            print(f"✓ Inserted {len(players)} players")

            # Sample matches
            print("Inserting sample matches...")
            base_time = datetime.now() - timedelta(days=1)
            matches = [
                ("match_001", "competitive", 9, base_time),
                ("match_002", "competitive", 9, base_time + timedelta(hours=1)),
                ("match_003", "competitive", 9, base_time + timedelta(hours=2)),
            ]

            for match_id, mode, season, match_timestamp in matches:
                cur.execute("""
                    INSERT INTO matches (match_id, mode, season, match_timestamp)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (match_id) DO NOTHING
                """, (match_id, mode, season, match_timestamp))

            print(f"✓ Inserted {len(matches)} matches")

            # Sample match participants
            print("Inserting sample match participants...")
            participants = [
                # Match 1 - Team 0 wins
                ("match_001", "SpiderGamer2024", 1001, "Spider-Man", "duelist", 0, True, 15, 3, 8, 25000.00, 0),
                ("match_001", "StrangeSupport", 1015, "Doctor Strange", "strategist", 0, True, 2, 1, 18, 8000.00, 32000.00),
                ("match_001", "IronDefender", 1009, "Iron Man", "duelist", 0, True, 12, 4, 10, 28000.00, 0),
                ("match_001", "ThorMain", 1020, "Thor", "vanguard", 1, False, 10, 8, 5, 18000.00, 0),
                ("match_001", "BlackWidowSniper", 1003, "Black Widow", "duelist", 1, False, 14, 7, 4, 22000.00, 0),

                # Match 2 - Team 1 wins
                ("match_002", "SpiderGamer2024", 1001, "Spider-Man", "duelist", 0, False, 11, 6, 7, 20000.00, 0),
                ("match_002", "IronDefender", 1004, "Captain America", "vanguard", 0, False, 8, 5, 9, 15000.00, 0),
                ("match_002", "ThorMain", 1020, "Thor", "vanguard", 1, True, 12, 3, 8, 24000.00, 0),
                ("match_002", "BlackWidowSniper", 1003, "Black Widow", "duelist", 1, True, 18, 4, 6, 30000.00, 0),
                ("match_002", "StrangeSupport", 1015, "Doctor Strange", "strategist", 1, True, 3, 2, 15, 9000.00, 28000.00),

                # Match 3 - Team 0 wins
                ("match_003", "ThorMain", 1020, "Thor", "vanguard", 0, True, 9, 2, 12, 18000.00, 0),
                ("match_003", "BlackWidowSniper", 1007, "Hawkeye", "duelist", 0, True, 16, 3, 8, 27000.00, 0),
                ("match_003", "StrangeSupport", 1026, "Luna Snow", "strategist", 0, True, 1, 1, 20, 5000.00, 35000.00),
                ("match_003", "SpiderGamer2024", 1010, "Star-Lord", "duelist", 1, False, 13, 7, 5, 23000.00, 0),
                ("match_003", "IronDefender", 1004, "Captain America", "vanguard", 1, False, 7, 6, 8, 14000.00, 0),
            ]

            for participant_data in participants:
                cur.execute("""
                    INSERT INTO match_participants
                    (match_id, username, hero_id, hero_name, role, team, won, kills, deaths, assists, damage, healing)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (match_id, username) DO NOTHING
                """, participant_data)

            print(f"✓ Inserted {len(participants)} match participants")

            # Commit all changes
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

            print()
            print("✓ Sample data seeded successfully!")
            print()

    except psycopg2.Error as e:
        conn.rollback()
        print(f"✗ Failed to seed data: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
