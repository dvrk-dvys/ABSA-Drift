#!/usr/bin/env python3
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
import argparse

def load_parquet_to_db(file_path: str,
                       table_name: str,
                       connection_string: str,
                       if_exists: str = 'replace'):
    # 1) Read parquet
    df = pd.read_parquet(file_path)
    print(f"✅ Loaded {len(df)} rows × {len(df.columns)} columns")
    print("   Columns:", df.columns.tolist())

    # 2) Normalize column names: lower + underscores
    df.columns = (
        df.columns
          .str.lower()
          .str.replace(r'[ \-]+', '_', regex=True)
    )
    print("🔤 Normalized columns:", df.columns.tolist())

    # 3) Detect array‑type columns (lists/tuples/ndarrays)
    array_cols = []
    for col in df.columns:
        if df[col].dtype == 'object':
            non_null = df[col].dropna()
            # sample up to 5 non‑nulls
            sample_values = non_null.head(min(len(non_null), 5))
            if len(sample_values) > 0 and all(isinstance(v, (list, tuple, np.ndarray)) for v in sample_values):
                array_cols.append(col)
    print("🗂️ Detected array columns:", array_cols)

    # 4) Convert any numpy arrays → plain Python lists
    for col in array_cols:
        print(f"   ↪ Converting `{col}` to lists…")
        df[col] = df[col].apply(lambda arr: None
                                if arr is None else
                                arr.tolist() if isinstance(arr, np.ndarray) else
                                list(arr)    if isinstance(arr, (list, tuple)) else
                                arr)
    print("✅ Finished normalizing array columns")

    # 5) Write to Postgres, storing arrays as JSONB
    engine = create_engine(connection_string)
    dtype_map = {col: JSONB() for col in array_cols}

    df.to_sql(
        table_name,
        engine,
        if_exists=if_exists,
        index=False,
        chunksize=10_000,
        dtype=dtype_map
    )
    print(f"🚀 Written to table `{table_name}` (if_exists='{if_exists}')")
    print(f"   JSONB array columns: {array_cols}")


if __name__ == "__main__":
    # file paths & defaults
    original_csv    = "/Users/jordanharris/Code/ABSA-Drift/data/raw/TTCommentExporter-7522631316479790391-3522-comments-replies.csv"
    default_parquet = "/Users/jordanharris/Code/ABSA-Drift/data/raw/absa_debug_train_dataframe.parquet"
    default_table   = "tiktok_comments_nlp"

    # argparse for the loader
    parser = argparse.ArgumentParser(description="Load ABSA-Drift parquet into Postgres")
    parser.add_argument('--file_path',  default=default_parquet,
                        help="Parquet file to load")
    parser.add_argument('--table_name', default=default_table,
                        help="Postgres table name")
    parser.add_argument('--host',       default='localhost')
    parser.add_argument('--port',       default=5432, type=int)
    parser.add_argument('--database',   default='absa_db')
    parser.add_argument('--username',   default='absa_user')
    parser.add_argument('--password',   default='absa_password')
    parser.add_argument('--if-exists',  dest='if_exists',
                        choices=['fail','replace','append'],
                        default='replace',
                        help="`to_sql` if_exists behavior")
    args = parser.parse_args()

    # build connection string
    conn_str = (
        f"postgresql://{args.username}:"
        f"{args.password}@{args.host}:"
        f"{args.port}/{args.database}"
    )

    # run the loader
    load_parquet_to_db(
        file_path=args.file_path,
        table_name=args.table_name,
        connection_string=conn_str,
        if_exists=args.if_exists
    )

    # === diagnostics ===
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 0)

    print("\n📊 Raw CSV stats (Digg/Reply):")
    raw_csv = pd.read_csv(original_csv, usecols=['Digg Count','Reply Count'])
    print(raw_csv.describe())

    print("\n📊 Parquet stats (Digg/Reply):")
    pq = pd.read_parquet(args.file_path)
    print(pq[['Digg Count','Reply Count']].describe())
