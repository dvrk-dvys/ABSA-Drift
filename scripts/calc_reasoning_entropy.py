import argparse
import math
from collections import Counter

import pandas as pd
from sqlalchemy import create_engine, text

def calc_shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    tokens = text.split()
    total = len(tokens)
    counts = Counter(tokens)
    return -sum((cnt/total) * math.log2(cnt/total) for cnt in counts.values())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Add reasoning_shannon_entropy column to an existing Postgres table'
    )
    parser.add_argument('--table_name',
                        default='tiktok_comments_nlp',
                        help='Postgres table to update')
    parser.add_argument('--host', default='localhost', help='DB host')
    parser.add_argument('--port', default=5432, type=int, help='DB port')
    parser.add_argument('--database', default='absa_db', help='DB name')
    parser.add_argument('--username', default='absa_user', help='DB user')
    parser.add_argument('--password', default='absa_password', help='DB password')
    args = parser.parse_args()

    conn_str = (
        f"postgresql://{args.username}:"
        f"{args.password}@{args.host}:"
        f"{args.port}/{args.database}"
    )
    engine = create_engine(conn_str)

    # 1) add the new column if it doesn't already exist
    with engine.begin() as conn:
        conn.execute(text(
            f"ALTER TABLE {args.table_name} "
            "ADD COLUMN IF NOT EXISTS reasoning_shannon_entropy DOUBLE PRECISION"
        ))

    # 2) load primary key and reasoning text
    df = pd.read_sql(
        f"SELECT comment_id, reasoning FROM {args.table_name}",
        con=engine
    )

    # 3) compute entropy
    df['reasoning_shannon_entropy'] = (
        df['reasoning']
          .fillna('')
          .apply(calc_shannon_entropy)
    )

    # 4) update each row’s new column
    with engine.begin() as conn:
        for cid, entropy in zip(df['comment_id'], df['reasoning_shannon_entropy']):
            conn.execute(
                text(
                    f"UPDATE {args.table_name} "
                    "SET reasoning_shannon_entropy = :entropy "
                    "WHERE comment_id = :comment_id"
                ),
                {
                    "entropy": float(entropy),
                    # pass the ID as a string, not int()
                    "comment_id": str(cid)
                }
            )
