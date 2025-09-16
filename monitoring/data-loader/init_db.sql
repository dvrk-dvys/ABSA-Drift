-- ABSA Data for Grafana


DROP TABLE IF EXISTS absa_monitoring_data;
DROP TABLE IF EXISTS absa_drift_summary;


CREATE TABLE absa_monitoring_data (
    id SERIAL PRIMARY KEY,
    comment_id BIGINT NOT NULL,
    comment_text TEXT,
    aspectterm VARCHAR(255),
    comment_time TIMESTAMP WITH TIME ZONE,
    polarity INTEGER,
    implicitness BOOLEAN,
    sentiment_score FLOAT,
    engagement_score FLOAT,
    implicitness_degree FLOAT,
    cluster_id VARCHAR(50),
    loaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(comment_id, aspectterm)
);


CREATE TABLE absa_drift_summary (
    id SERIAL PRIMARY KEY,
    summary_date DATE NOT NULL,
    hour_bucket INTEGER NOT NULL,
    total_comments INTEGER DEFAULT 0,
    avg_sentiment_score FLOAT,
    avg_engagement_score FLOAT,
    positive_count INTEGER DEFAULT 0,
    neutral_count INTEGER DEFAULT 0,
    negative_count INTEGER DEFAULT 0,
    implicit_count INTEGER DEFAULT 0,
    explicit_count INTEGER DEFAULT 0,
    top_aspects TEXT[],
    unique_clusters INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(summary_date, hour_bucket)
);


CREATE INDEX idx_monitoring_comment_time ON absa_monitoring_data(comment_time);
CREATE INDEX idx_monitoring_aspectterm ON absa_monitoring_data(aspectterm);
CREATE INDEX idx_monitoring_polarity ON absa_monitoring_data(polarity);
CREATE INDEX idx_summary_date_hour ON absa_drift_summary(summary_date, hour_bucket);