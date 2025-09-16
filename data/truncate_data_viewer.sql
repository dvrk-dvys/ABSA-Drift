SELECT

    LEFT(aspectterm, 15) AS aspectterm,
    LEFT(comment, 40) AS comment,
    comment_id,
    reply_to_which_comment,
    user_id,
    LEFT(username, 15) AS username,
    LEFT(nick_name, 15) AS nick_name,
    comment_time,


    digg_count,
    author_digged,
    reply_count,
    pinned_to_top,
    LEFT(user_homepage, 30) AS user_homepage,
    shannon_entropy,
    index,
    mutual_information_score,
    surprisal,
    perplexity,
    contextual_mutual_information_score,
    contextual_surprisal,
    contextual_perplexity,


    CASE
        WHEN jsonb_typeof(input_ids::jsonb) = 'array'
        THEN jsonb_array_length(input_ids::jsonb)
        ELSE NULL
    END AS input_len,
    LEFT(input_ids::text, 30) || '...' AS input_preview,

    CASE
        WHEN jsonb_typeof(token_type_ids::jsonb) = 'array'
        THEN jsonb_array_length(token_type_ids::jsonb)
        ELSE NULL
    END AS token_type_len,

    CASE
        WHEN jsonb_typeof(attention_mask::jsonb) = 'array'
        THEN jsonb_array_length(attention_mask::jsonb)
        ELSE NULL
    END AS attn_len,

    CASE
        WHEN jsonb_typeof(spacy_tokens::jsonb) = 'array'
        THEN jsonb_array_length(spacy_tokens::jsonb)
        ELSE NULL
    END AS token_count,
    LEFT(spacy_tokens::text, 40) || '...' AS tokens_preview,

    CASE
        WHEN jsonb_typeof(pos::jsonb) = 'array'
        THEN jsonb_array_length(pos::jsonb)
        ELSE NULL
    END AS pos_len,

    CASE
        WHEN jsonb_typeof(pos_tags::jsonb) = 'array'
        THEN jsonb_array_length(pos_tags::jsonb)
        ELSE NULL
    END AS pos_tag_len,

    CASE
        WHEN jsonb_typeof(entities::jsonb) = 'array'
        THEN jsonb_array_length(entities::jsonb)
        ELSE NULL
    END AS entity_len,

    CASE
        WHEN jsonb_typeof(heads::jsonb) = 'array'
        THEN jsonb_array_length(heads::jsonb)
        ELSE NULL
    END AS heads_len,

    CASE
        WHEN jsonb_typeof(labels::jsonb) = 'array'
        THEN jsonb_array_length(labels::jsonb)
        ELSE NULL
    END AS labels_len,

    CASE
        WHEN jsonb_typeof(dependencies::jsonb) = 'array'
        THEN jsonb_array_length(dependencies::jsonb)
        ELSE NULL
    END AS deps_len,

    CASE
        WHEN jsonb_typeof(negations::jsonb) = 'array'
        THEN jsonb_array_length(negations::jsonb)
        ELSE NULL
    END AS neg_len,


    LEFT(lda_aspect_prob, 50) || '...' AS lda_preview,

    CASE
        WHEN jsonb_typeof(aspect_mask::jsonb) = 'array'
        THEN jsonb_array_length(aspect_mask::jsonb)
        ELSE NULL
    END AS mask_len,


    implicitness,
    polarity,

    CASE
        WHEN jsonb_typeof(token_ids::jsonb) = 'array'
        THEN jsonb_array_length(token_ids::jsonb)
        ELSE NULL
    END AS token_ids_len,

    LEFT(raw_text, 50) AS raw_text,
    LEFT(reasoning, 60) || '...' AS reasoning

FROM tiktok_comments_nlp
ORDER BY index DESC
LIMIT 50;