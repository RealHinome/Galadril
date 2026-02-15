use std::sync::Arc;

use anyhow::{Result, anyhow};
use chrono::Utc;
use uuid::Uuid;

use crate::domain::models::OsintArticle;
use crate::domain::ports::EventProducer;

pub struct JsonOsintParser;

impl JsonOsintParser {
    pub async fn parse_and_publish(
        content: &[u8],
        producer: &Arc<dyn EventProducer>,
    ) -> Result<()> {
        let articles: Vec<RawOsintArticle> = serde_json::from_slice::<
            Vec<RawOsintArticle>,
        >(content)
        .or_else(|_| {
            serde_json::from_slice::<RawOsintArticle>(content).map(|a| vec![a])
        })?;

        for raw in articles {
            let article = Self::validate_and_map(raw)?;
            producer.publish_osint(article).await?;
        }

        Ok(())
    }

    fn validate_and_map(raw: RawOsintArticle) -> Result<OsintArticle> {
        if raw.url.is_empty() {
            return Err(anyhow!("OSINT article missing URL"));
        }

        if raw.content_raw.is_empty() {
            return Err(anyhow!("OSINT article has no content: {}", raw.url));
        }

        Ok(OsintArticle {
            article_id: Uuid::new_v4().to_string(),
            url: raw.url,
            source_domain: raw.source_domain.unwrap_or_default(),
            published_at: raw.published_at,
            collected_at: Utc::now(),
            title: raw.title,
            content_raw: raw.content_raw,
            author: raw.author,
            language: raw.language,
        })
    }
}

#[derive(Debug, serde::Deserialize)]
struct RawOsintArticle {
    url: String,
    source_domain: Option<String>,
    published_at: Option<chrono::DateTime<Utc>>,
    title: Option<String>,
    content_raw: String,
    author: Option<String>,
    language: Option<String>,
}
