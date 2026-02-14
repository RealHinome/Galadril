# Galadril ⛲️

> *"Things that were, and things that are, and some things that have not yet
> come to pass."*

**Galadril** is an advanced data integration and analytical intelligence
platform designed to provide a "Mirror" of complex systems. Galadril focuses
on **elucidation, foresight, and transparency**.

> [!CAUTION]
> This project is still in its early stages.

## Targeted architecture

```mermaid
graph TD

    classDef rust fill:#dea584,stroke:#000,stroke-width:2px,color:#000;
    classDef go fill:#00add8,stroke:#000,stroke-width:2px,color:#000;
    classDef python fill:#3572A5,stroke:#fff,stroke-width:2px,color:#fff;
    classDef storage fill:#222,stroke:#fff,stroke-width:1px,color:#fff;
    classDef streaming fill:#ff4500,stroke:#000,stroke-width:1px,color:#fff;
    classDef interface fill:#f4f4f4,stroke:#333,stroke-width:2px,color:#333;

    subgraph Sources["Data Sources"]
        Sat[Satellite Imagery]
        Fin[Financial Flows]
        Osint[OSINT / News]
    end

    subgraph Intake["Ingestion & Contract Enforcement"]
        IntakeSvc["Rust Intake Services"]:::rust
        Contract["Schema Validation / Data Contracts"]:::rust
    end

    subgraph Streaming["Streaming Backbone (Multi-tier)"]
        KafkaRaw["Kafka RAW Topics"]:::streaming
        FlinkEnrich["Flink Enrichment / Normalization"]:::streaming
        KafkaCurated["Kafka CURATED Topics"]:::streaming
        FlinkIntel["Flink Intelligence Processing"]:::streaming
        KafkaIntel["Kafka INTELLIGENCE Topics"]:::streaming
    end

    subgraph Storage["The Mirror (Data Platform)"]
        Iceberg["Data Lake (Iceberg Tables)"]:::storage
        GraphDB["Graph Database"]:::storage
        VectorDB["Vector Database"]:::storage
    end

    subgraph FeaturePlatform["Feature Store Platform"]
        FSOnline["Feature Store Online"]:::go
        FSOffline["Feature Store Offline"]:::python
    end

    subgraph MLPlatform["The Vision (ML Platform)"]
        Training["Model Training Pipelines"]:::python
        Registry["Model Registry / Versioning"]:::python
        Inference["Realtime Inference Services"]:::python
        Drift["Drift Detection / Monitoring"]:::python
    end

    subgraph Orchestration["Workflow & Orchestration"]
        Airflow["Airflow Orchestrator"]:::python
    end

    subgraph Delivery["Serving & API Layer"]
        RealtimeAPI["API Gateway & WebSockets (Go)"]:::go
        Dashboard["Galadril Studio (React / D3)"]:::interface
    end

    Sat --> IntakeSvc
    Fin --> IntakeSvc
    Osint --> IntakeSvc

    IntakeSvc --> Contract
    Contract --> KafkaRaw

    KafkaRaw --> FlinkEnrich
    FlinkEnrich --> KafkaCurated
    KafkaCurated --> FlinkIntel
    FlinkIntel --> KafkaIntel

    KafkaCurated --> Iceberg
    KafkaIntel --> GraphDB
    KafkaIntel --> VectorDB

    Iceberg --> FSOffline
    KafkaCurated --> FSOnline

    FSOffline --> Training
    Training --> Registry
    Registry --> Inference

    FSOnline --> Inference
    Inference --> Drift

    Airflow --> Training
    Airflow --> FSOffline
    Airflow --> Iceberg

    Inference --> RealtimeAPI
    KafkaIntel --> RealtimeAPI

    RealtimeAPI --> Dashboard
```
