# Store aspect vectors with timestamps
aspect_vector_v1 = {
    "timestamp": "2024-01-01",
    "aspect": "battery",
    "vector": [sentiment_avg, engagement_avg, implicitness_rate],
    "metadata": {"week": 1, "month": 1}
}

aspect_vector_v2 = {
    "timestamp": "2024-01-15",
    "aspect": "battery",
    "vector": [sentiment_avg, engagement_avg, implicitness_rate],
    "metadata": {"week": 3, "month": 1}
}

SELECT
count(user_id) as commenter_frequency,
user_id
FROM public.tiktok_comments_nlp as nlp
group by user_id
order by commenter_frequency desc