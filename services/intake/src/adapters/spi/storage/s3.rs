//! Amazon S3 (or all S3-like) adapter.

use anyhow::{Context, Result};
use async_trait::async_trait;
use aws_sdk_s3::Client;
use aws_sdk_s3::primitives::ByteStream;

use crate::domain::ports::BlobStorage;

pub struct S3Adapter {
    client: Client,
    bucket: String,
}

impl S3Adapter {
    /// Create a new [`S3Adapter`].
    pub async fn new(endpoint: &str, bucket: &str) -> Result<Self> {
        let config =
            aws_config::from_env().endpoint_url(endpoint).load().await;

        let s3_config = aws_sdk_s3::config::Builder::from(&config)
            .force_path_style(true)
            .build();

        let client = Client::from_conf(s3_config);

        client
            .head_bucket()
            .bucket(bucket)
            .send()
            .await
            .context(format!("Bucket {bucket:?} not reachable"))?;

        Ok(Self {
            client,
            bucket: bucket.to_string(),
        })
    }
}

#[async_trait]
impl BlobStorage for S3Adapter {
    async fn upload_file(
        &self,
        file_name: &str,
        data: &[u8],
    ) -> Result<String> {
        let body = ByteStream::from(data.to_vec());
        self.client
            .put_object()
            .bucket(&self.bucket)
            .key(file_name)
            .body(body)
            .send()
            .await
            .context(format!("Failed to upload {file_name:?}"))?;

        Ok(format!("s3://{}/{file_name}", self.bucket))
    }

    async fn download_file(&self, key: &str) -> Result<Vec<u8>> {
        let response = self
            .client
            .get_object()
            .bucket(&self.bucket)
            .key(key)
            .send()
            .await?;

        let bytes = response.body.collect().await?.into_bytes().to_vec();

        Ok(bytes)
    }
}
