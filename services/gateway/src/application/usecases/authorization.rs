//! Authorization use cases using Cedar and AGE graphs.

use std::collections::{HashMap, HashSet};
use std::str::FromStr;
use std::sync::Arc;

use anyhow::{Context, Result};
use cedar_policy::{
    Authorizer, Context as CedarContext, Entities, Entity, EntityId,
    EntityTypeName, EntityUid, PolicyId, PolicySet, Request,
};

use crate::application::ports::entity_provider::EntityGraphProvider;
use crate::application::ports::policy_store::PolicyStore;

/// Action types mapped to Cedar actions.
pub enum Action {
    ReadSink,
    DiscoverSinks,
}

impl Action {
    fn as_str(&self) -> &'static str {
        match self {
            Action::ReadSink => "Action::\"Read\"",
            Action::DiscoverSinks => "Action::\"Discover\"",
        }
    }
}

/// Service responsible for evaluating access control.
pub struct AuthService {
    policy_store: Arc<dyn PolicyStore>,
    entity_provider: Arc<dyn EntityGraphProvider>,
}

impl AuthService {
    /// Creates a new [`AuthService`].
    pub fn new(
        policy_store: Arc<dyn PolicyStore>,
        entity_provider: Arc<dyn EntityGraphProvider>,
    ) -> Self {
        Self {
            policy_store,
            entity_provider,
        }
    }

    /// Evaluates if a user (principal) can perform an action on a specific
    /// resource.
    pub async fn is_authorized(
        &self,
        user_id: &str,
        action: Action,
        resource_name: &str,
    ) -> Result<bool> {
        let records = self.policy_store.get_active_policies().await?;
        let mut policy_set = PolicySet::new();

        for record in records {
            let policy = cedar_policy::Policy::parse(
                Some(PolicyId::new(&record.id)),
                &record.content,
            )
            .with_context(|| {
                format!("Failed to parse Cedar policy ID: {}", record.id)
            })?;
            policy_set.add(policy).with_context(|| {
                format!("Failed to add policy ID: {}", record.id)
            })?;
        }

        let graph_nodes = self.entity_provider.get_entity_graph().await?;
        let mut cedar_entities = Vec::new();

        for node in graph_nodes {
            let type_name = EntityTypeName::from_str(&node.entity_type)
                .with_context(|| {
                    format!("Invalid entity type: {}", node.entity_type)
                })?;
            let entity_id =
                EntityId::from_str(&node.entity_id).with_context(|| {
                    format!("Invalid entity ID: {}", node.entity_id)
                })?;

            let uid = EntityUid::from_type_name_and_id(type_name, entity_id);

            let mut parents = HashSet::new();
            for parent_ref in node.parents {
                let p_type = EntityTypeName::from_str(&parent_ref.entity_type)
                    .with_context(|| {
                        format!(
                            "Invalid parent type: {}",
                            parent_ref.entity_type
                        )
                    })?;
                let p_id = EntityId::from_str(&parent_ref.entity_id)
                    .with_context(|| {
                        format!("Invalid parent ID: {}", parent_ref.entity_id)
                    })?;
                parents.insert(EntityUid::from_type_name_and_id(p_type, p_id));
            }

            let entity = Entity::new(uid, HashMap::new(), parents)
                .context("Failed to construct Cedar entity")?;

            cedar_entities.push(entity);
        }

        let entities = Entities::from_entities(cedar_entities, None)
            .context("Failed to build Cedar Entities store")?;

        let principal = EntityUid::from_str(&format!("User::\"{}\"", user_id))
            .context("Invalid principal UID format")?;
        let action_uid = EntityUid::from_str(action.as_str())
            .context("Invalid action UID format")?;
        let resource =
            EntityUid::from_str(&format!("Sink::\"{}\"", resource_name))
                .context("Invalid resource UID format")?;

        let request = Request::new(
            principal,
            action_uid,
            resource,
            CedarContext::empty(),
            None,
        )
        .context("Failed to construct Cedar request")?;

        let authorizer = Authorizer::new();
        let response =
            authorizer.is_authorized(&request, &policy_set, &entities);

        Ok(response.decision() == cedar_policy::Decision::Allow)
    }
}
