import pandas as pd
import numpy as np
from sqlalchemy import create_engine

def load_data_from_postgres(
    table_name: str = 'tiktok_comments_nlp',
    host: str = 'localhost',
    port: int = 5432,
    database: str = 'absa_db',
    username: str = 'absa_user',
    password: str = 'absa_password'
) -> pd.DataFrame:
    """Load data from PostgreSQL database"""
    conn_str = f"postgresql://{username}:{password}@{host}:{port}/{database}"
    engine = create_engine(conn_str)
    
    sql = f"""
        SELECT
          comment_id,
          reply_to_which_comment,
          comment_time,
          aspectterm,
          implicitness,
          polarity, 
          comment,
          reasoning,
          --aspect_mask,
          --input_ids,
          --attention_mask,
          digg_count,
          reply_count,
          shannon_entropy,
          reasoning_shannon_entropy,
          mutual_information_score,
          surprisal,
          perplexity
        FROM {table_name}
    """
    
    df = pd.read_sql(sql, con=engine)
    return df

def create_implicitness_degree(df: pd.DataFrame,
                               w_entropy: float = 0.4,
                               w_surprisal: float = 0.4,
                               w_reasoning: float = 0.2,
                               floor_explicit: float = 0.1) -> pd.Series:
    e = df['shannon_entropy']
    s = df['surprisal']
    r = df['reasoning_shannon_entropy'].fillna(0.0)

    e_n = (e - e.min())/(e.max()-e.min()) if e.max()>e.min() else 0
    s_n = (s - s.min())/(s.max()-s.min()) if s.max()>s.min() else 0
    r_n = (r - r.min())/(r.max()-r.min()) if r.max()>r.min() else 0

    raw = pd.Series(index=df.index, dtype=float)
    explicit = ~df['implicitness']
    raw[explicit] = floor_explicit
    
    implicit = df['implicitness']
    raw[implicit] = w_entropy * e_n[implicit] + w_surprisal * s_n[implicit] + w_reasoning * r_n[implicit]
    
    return raw

def create_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Create advanced target variables for training"""
    targets = pd.DataFrame(index=df.index)
    
    # sentiment score: map polarity to -1 to +1 range
    targets['sentiment_score'] = df['polarity'].map({0: 1.0, 1: -1.0, 2: 0.0})
    
    # engagement score: log1p (log(1+x)) to ensure non-negative values
    targets['engagement_score'] = np.log1p(df['digg_count'].fillna(0))
    
    # implicitness degree
    targets['implicitness_degree'] = create_implicitness_degree(df)
    
    return targets



def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create features for training/inference - only core linguistic and context features"""
    
    num_cols = ['shannon_entropy', 'mutual_information_score', 'surprisal', 'perplexity']
    feats = df[num_cols].copy()

    feats['is_reply'] = df['reply_to_which_comment'].notna().astype(int)
    feats['has_replies'] = (df['reply_count'].fillna(0) > 0).astype(int)
    feats['reply_count'] = df['reply_count'].fillna(0)

    feats['digg_count'] = df['digg_count'].fillna(0)

    return feats

