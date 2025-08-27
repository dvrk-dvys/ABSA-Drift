import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from transformers import AutoTokenizer, AutoModel
import torch
from typing import Optional, Dict, Any

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
          aspect_mask,
          input_ids,
          attention_mask,
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
    """Create implicitness degree score"""
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

def create_aspect_summaries(aspect_mask_series: pd.Series) -> pd.DataFrame:
    """Create aspect summary features from aspect masks"""
    summaries = []
    
    for idx, mask_str in aspect_mask_series.items():
        try:
            if pd.isna(mask_str) or (isinstance(mask_str, str) and mask_str == ''):
                # no aspects
                summary = {f'aspect_{i}_count': 0 for i in range(5)}
                summary.update({f'aspect_{i}_present': 0 for i in range(5)})
            else:
                mask_list = eval(mask_str) if isinstance(mask_str, str) else mask_str
                if not isinstance(mask_list, list):
                    mask_list = [0] * 5
                
                # pad or truncate to 5 aspects
                mask_list = mask_list[:5] + [0] * (5 - len(mask_list))
                
                summary = {}
                for i, count in enumerate(mask_list):
                    summary[f'aspect_{i}_count'] = count
                    summary[f'aspect_{i}_present'] = 1 if count > 0 else 0
        except:
            # fallback
            summary = {f'aspect_{i}_count': 0 for i in range(5)}
            summary.update({f'aspect_{i}_present': 0 for i in range(5)})
        
        summaries.append(summary)
    
    return pd.DataFrame(summaries, index=aspect_mask_series.index)

def create_features(df: pd.DataFrame,
                    embed_model: torch.nn.Module,
                    tokenizer: AutoTokenizer) -> pd.DataFrame:
    """Create features for training/inference"""
    # numerical & linguistic
    feats = pd.DataFrame(index=df.index)
    num_cols = ['shannon_entropy', 'mutual_information_score', 'surprisal', 'perplexity', 'implicitness']
    feats[num_cols] = df[num_cols]

    # reply context
    feats['is_reply'] = df['reply_to_which_comment'].notna().astype(int)
    feats['has_replies'] = (df['reply_count'].fillna(0) > 0).astype(int)

    # implicitness boolean
    feats['implicit'] = df['implicitness'].astype(int)

    # aspect summaries
    aspect_summ = create_aspect_summaries(df['aspect_mask'])
    feats = pd.concat([feats, aspect_summ], axis=1)

    # embed reasoning using transformer
    embed_dim = embed_model.config.hidden_size
    all_emb = np.zeros((len(df), embed_dim), dtype=float)
    embed_model.eval()

    for i in range(len(df)):
        ids = df['input_ids'].iloc[i]
        mask = df['attention_mask'].iloc[i]
        
        if ids is None or mask is None:
            # Use dummy embeddings (zeros) for missing data
            vec = np.zeros(embed_dim)
        else:
            input_ids = torch.tensor([ids])
            attention_mask = torch.tensor([mask])
            with torch.no_grad():
                out = embed_model(input_ids=input_ids, attention_mask=attention_mask)
            vec = out.last_hidden_state[:, 0, :].cpu().numpy().flatten()
        all_emb[i] = vec
    
    emb_df = pd.DataFrame(all_emb, index=df.index, columns=[f'emb_{j}' for j in range(embed_dim)])
    feats = pd.concat([feats, emb_df], axis=1)

    return feats

def load_nlp_models(model_name: str = 'bert-base-uncased'):
    """Load tokenizer and embedding model"""
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    embed_model = AutoModel.from_pretrained(model_name)
    return tokenizer, embed_model