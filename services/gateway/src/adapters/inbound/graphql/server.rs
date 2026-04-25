//! Axum HTTP and WebSocket server for GraphQL.

use std::sync::Arc;

use axum::{
    Router,
    extract::{Extension, WebSocketUpgrade},
    response::IntoResponse,
    routing::{get, post},
};

use juniper_axum::{
    extract::JuniperRequest, response::JuniperResponse, subscriptions,
};

use juniper_graphql_ws::ConnectionConfig;

use crate::adapters::inbound::graphql::auth::Claims;
use crate::adapters::inbound::graphql::context::AppContext;
use crate::adapters::inbound::graphql::schema::{AppSchema, create_schema};
use crate::application::usecases::data_explorer::DataExplorerService;

/// Bootstraps the Axum router with GraphQL endpoints.
pub fn create_router(data_explorer: Arc<DataExplorerService>) -> Router {
    let schema = Arc::new(create_schema());

    Router::new()
        .route("/graphql", post(graphql_handler).get(graphql_ws))
        .route(
            "/graphiql",
            get(juniper_axum::graphiql("/graphql", "/graphql")),
        )
        .route(
            "/playground",
            get(juniper_axum::playground("/graphql", "/graphql")),
        )
        .layer(Extension(schema))
        .layer(Extension(data_explorer))
}

/// Handles standard GraphQL POST requests.
async fn graphql_handler(
    Extension(schema): Extension<Arc<AppSchema>>,
    Extension(data_explorer): Extension<Arc<DataExplorerService>>,
    claims: Claims,
    JuniperRequest(req): JuniperRequest,
) -> JuniperResponse {
    let context = AppContext {
        user_id: claims.sub,
        data_explorer,
    };
    let response = req.execute(&*schema, &context).await;
    JuniperResponse(response)
}

/// Handles GraphQL WebSocket subscriptions.
async fn graphql_ws(
    Extension(schema): Extension<Arc<AppSchema>>,
    Extension(data_explorer): Extension<Arc<DataExplorerService>>,
    ws: WebSocketUpgrade,
) -> impl IntoResponse {
    // TODO: since JWT is not still implemented in WS, use a hard-coded user.
    let context = AppContext {
        user_id: "ws_user".to_string(),
        data_explorer,
    };

    ws.on_upgrade(|socket| async move {
        let config = ConnectionConfig::new(context);
        subscriptions::serve_graphql_ws(socket, schema, config).await;
    })
}
