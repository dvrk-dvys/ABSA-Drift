import os
import shutil
import pandas as pd
from sqlalchemy import create_engine, text
import argparse


def load_csv_replies(csv_path: str) -> pd.DataFrame:
    """
    Load and clean reply counts from the raw CSV.
    Returns DataFrame with columns ['comment_id', 'reply_count'].
    """
    df = pd.read_csv(
        csv_path,
        usecols=['Comment ID', 'Reply Count'],
        dtype={'Comment ID': str}
    )
    # normalize
    df.columns = (
        df.columns
          .str.lower()
          .str.replace(r'[ \-]+', '_', regex=True)
    )
    # clean ids
    df['comment_id'] = (
        df['comment_id']
          .str.strip()
          .str.lstrip('=')
          .str.strip('"')
    )
    # numeric counts
    df['reply_count'] = pd.to_numeric(df['reply_count'], errors='coerce')
    return df[['comment_id', 'reply_count']]


def update_postgres_replies(df_replies: pd.DataFrame,
                            table_name: str,
                            connection_string: str) -> None:
    """
    Update the Postgres table's reply_count column using df_replies.
    """
    engine = create_engine(connection_string)
    print(f"🔄 Updating Postgres table '{table_name}'...")
    stmt = text(f"""
        UPDATE {table_name} AS t
        SET reply_count = CAST(c.reply_count AS double precision)
        FROM (VALUES (:id, :rc)) AS c(comment_id, reply_count)
        WHERE t.comment_id = c.comment_id;
    """
    )
    with engine.begin() as conn:
        for id_, rc in zip(df_replies['comment_id'], df_replies['reply_count']):
            conn.execute(stmt, {'id': id_, 'rc': float(rc) if pd.notna(rc) else None})
    print("✅ Postgres update complete.")


def update_parquet_replies(input_path: str,
                           output_path: str,
                           df_replies: pd.DataFrame) -> None:
    """
    Read existing Parquet, merge in reply counts, and write new Parquet to output_path.
    """
    print(f"📂 Reading Parquet from '{input_path}'...")
    df_pq = pd.read_parquet(input_path)
    df_pq.columns = (
        df_pq.columns
             .str.lower()
             .str.replace(r'[ \-]+', '_', regex=True)
    )
    print("🔗 Merging reply counts into Parquet DataFrame...")
    df_merged = df_pq.merge(
        df_replies,
        on='comment_id',
        how='left',
        suffixes=('', '_new')
    )
    df_merged['reply_count'] = df_merged['reply_count_new'].combine_first(df_merged['reply_count'])
    df_merged.drop(columns=['reply_count_new'], inplace=True)

    # prepare output
    if os.path.exists(output_path):
        if os.path.isdir(output_path):
            shutil.rmtree(output_path)
        else:
            os.remove(output_path)

    print(f"💾 Writing updated Parquet to '{output_path}'...")
    df_merged.to_parquet(output_path, index=False)
    print("✅ Parquet update complete.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Update reply counts from raw CSV into Postgres and Parquet'
    )
    parser.add_argument('--original_csv',
                        default='/Users/jordanharris/Code/ABSA-Drift/data/raw/TTCommentExporter-7522631316479790391-3522-comments-replies.csv',
                        help='Path to raw CSV file')
    parser.add_argument('--input_parquet',
                        default='/Users/jordanharris/Code/ABSA-Drift/data/raw/absa_debug_train_dataframe.parquet',
                        help='Path to target Parquet file')
    parser.add_argument('--output_parquet',
                        help='New Parquet file/directory for merged data')
    parser.add_argument('--table_name',
                        default='tiktok_comments_nlp',
                        help='Postgres table to update')
    parser.add_argument('--host', default='localhost', help='DB host')
    parser.add_argument('--port', default=5432, type=int, help='DB port')
    parser.add_argument('--database', default='absa_db', help='DB name')
    parser.add_argument('--username', default='absa_user', help='DB user')
    parser.add_argument('--password', default='absa_password', help='DB password')
    parser.add_argument('--if-exists', dest='if_exists',
                        choices=['fail', 'replace', 'append'],
                        default='replace',
                        help='Postgres to_sql if_exists behavior (unused here)')
    args = parser.parse_args()

    conn_str = (
        f"postgresql://{args.username}:"
        f"{args.password}@{args.host}:"
        f"{args.port}/{args.database}"
    )

    # update Postgres
    df_replies = load_csv_replies(args.original_csv)
    update_postgres_replies(df_replies, args.table_name, conn_str)

    base = args.input_parquet.rstrip('/')
    root = base[:-len('.parquet')]
    out_path = (args.output_parquet
                if args.output_parquet
                else f"{root}_with_replies.parquet")

    # merge and write Parquet
    update_parquet_replies(args.input_parquet, out_path, df_replies)

