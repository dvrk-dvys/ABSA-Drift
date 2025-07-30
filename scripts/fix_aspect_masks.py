#!/usr/bin/env python
import argparse
import json

import pandas as pd
from sqlalchemy import create_engine, text
from transformers import AutoTokenizer

def find_sublist_indices(lst, sub):
    """Return all start‐indices where `sub` appears as a contiguous sublist of `lst`."""
    n, m = len(lst), len(sub)
    return [i for i in range(n - m + 1) if lst[i : i + m] == sub]

if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description="Compute and upload aspect_mask for each row."
    )
    p.add_argument('--table_name', default='tiktok_comments_nlp')
    p.add_argument('--host',       default='localhost')
    p.add_argument('--port',       default=5432, type=int)
    p.add_argument('--database',   default='absa_db')
    p.add_argument('--username',   default='absa_user')
    p.add_argument('--password',   default='absa_password')
    args = p.parse_args()

    conn_str = (
        f"postgresql://{args.username}:"
        f"{args.password}@{args.host}:"
        f"{args.port}/{args.database}"
    )
    engine = create_engine(conn_str)

    # 1) add aspect_mask column (JSONB) if missing
    with engine.begin() as conn:
        conn.execute(text(f"""
            ALTER TABLE {args.table_name}
            ADD COLUMN IF NOT EXISTS aspect_mask JSONB
        """))

    # 2) load the rows we need
    df = pd.read_sql(
        f"SELECT comment_id, input_ids, aspectterm FROM {args.table_name}",
        con=engine
    )

    # 3) prepare a tokenizer for mapping aspectterm→input_ids subsequence
    tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')

    # 4) compute masks
    masks = {}
    for _, row in df.iterrows():
        cid = row['comment_id']
        input_ids = row['input_ids'] or []
        aspect = row['aspectterm'] or ''

        if aspect and input_ids:
            # get the token‐ids of the aspect term
            aspect_ids = tokenizer.encode(aspect, add_special_tokens=False)
            positions = find_sublist_indices(input_ids, aspect_ids)

            # build the mask
            mask = [0] * len(input_ids)
            for start in positions:
                for j in range(len(aspect_ids)):
                    mask[start + j] = 1
        else:
            mask = [0] * len(input_ids)

        masks[cid] = mask

    # 5) update back into Postgres
    stmt = text(f"""
        UPDATE {args.table_name}
           SET aspect_mask = :mask
         WHERE comment_id = :cid
    """)

    with engine.begin() as conn:
        for cid, mask in masks.items():
            conn.execute(stmt, {
                'cid': cid,
                'mask': json.dumps(mask)
            })

    print(f"✅ aspect_mask populated for {len(masks)} rows.")
