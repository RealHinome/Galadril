//! GraphQL context holding application services and user state.

use crate::application::usecases::data_explorer::DataExplorerService;
use std::sync::Arc;

/// The context shared across all GraphQL resolvers.
pub struct AppContext {
    /// The authenticated user's ID.
    pub user_id: String,
    pub data_explorer: Arc<DataExplorerService>,
}

impl juniper::Context for AppContext {}
