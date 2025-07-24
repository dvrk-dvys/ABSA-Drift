import pandas as pd
from sqlalchemy import create_engine
import argparse
from sqlalchemy.dialects.postgresql import JSONB


def load_parquet_to_db(file_path, table_name, connection_string, if_exists='replace'):
    df = pd.read_parquet(file_path)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    # normalize column names
    df.columns = [c.lower().replace(' ', '_').replace('-', '_') for c in df.columns]

    array_cols = [
        'token_ids', 'token_type_ids', 'attention_mask',
        'aspect_mask',  # etc.
    ]

    for col in array_cols:
        df[col] = df[col].apply(lambda arr: arr.tolist())

    engine = create_engine(connection_string)

    df.to_sql(
        table_name,
        engine,
        if_exists=if_exists,
        index=False,
        chunksize=10000,
        dtype={col: JSONB() for col in array_cols}  # only for Option B
    )

    print(f"Data loaded to table: {table_name}")



if __name__ == "__main__":
    raw_file_path="/Users/jordanharris/Code/ABSA-Drift/data/raw/debug_train_dataframe.parquet"
    table_name="tiktok_comments_nlp"

    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', default=raw_file_path)
    parser.add_argument('--table_name', default=table_name)
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', default=5432)
    parser.add_argument('--database', default='absa_db')
    parser.add_argument('--username', default='absa_user')
    parser.add_argument('--password', default='absa_password')
    parser.add_argument('--if-exists', default='replace', choices=['fail', 'replace', 'append'])

    args = parser.parse_args()

    connection_string = f'postgresql://{args.username}:{args.password}@{args.host}:{args.port}/{args.database}'

    load_parquet_to_db(args.file_path, args.table_name, connection_string, args.if_exists)
