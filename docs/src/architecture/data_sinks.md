# Data Sinks

When data reaches the end of Python pipeline DAG, it is saved into PostgreSQL.
Galadril uses two extensions to handle AI outputs.

## 1. Apache AGE (Graph Storage)

We use Apache AGE to store:
* **Vertices**: People, Bank Accounts, Documents.
* **Edges**: Relationships like `APPEARS_WITH` (Person A in Image B) or
    `TRANSACTED_WITH` (Account A sent money to Account B).

## 2. pgvectorscale (Embedding Storage)

AI models output embeddings representing faces or text. 
We use pgvectorscale to store these arrays and perform blazing-fast similarity
searches (e.g., finding the closest known face to an unknown detected face
using `ORDER BY embedding <=> query_vector`).