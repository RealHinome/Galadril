//! Authorization use cases using Cedar and AGE graphs with TTL caching.

use std::collections::{HashMap, HashSet};
use std::str::FromStr;
use std::sync::Arc;
use std::time::{Duration, Instant};

use anyhow::{Context, Result};
use cedar_policy::{
    Authorizer, Context as CedarContext, Entities, Entity, EntityId,
    EntityTypeName, EntityUid, PolicyId, PolicySet, Request,
};
use tokio::sync::RwLock;

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
            Action::ReadSink => "Read",
            Action::DiscoverSinks => "Discover",
        }
    }

    fn action_uid(&self) -> Result<EntityUid> {
        match self {
            Action::ReadSink => {
                EntityUid::from_str("Action::\"Read\"").map_err(Into::into)
            },
            Action::DiscoverSinks => {
                EntityUid::from_str("Action::\"Discover\"").map_err(Into::into)
            },
        }
    }
}

/// Internal cache structure for the Cedar environment.
struct AuthCache {
    policy_set: Arc<PolicySet>,
    entities: Arc<Entities>,
    expires_at: Instant,
}

/// Service responsible for evaluating access control with optimized caching.
pub struct AuthService {
    policy_store: Arc<dyn PolicyStore>,
    entity_provider: Arc<dyn EntityGraphProvider>,
    cache: RwLock<Option<AuthCache>>,
    cache_ttl: Duration,
}

impl AuthService {
    /// Creates a new [`AuthService`] with a specified cache TTL.
    pub fn new(
        policy_store: Arc<dyn PolicyStore>,
        entity_provider: Arc<dyn EntityGraphProvider>,
        cache_ttl: Duration,
    ) -> Self {
        Self {
            policy_store,
            entity_provider,
            cache: RwLock::new(None),
            cache_ttl,
        }
    }

    /// Invalidates the cache.
    pub async fn invalidate_cache(&self) {
        let mut cache_guard = self.cache.write().await;
        *cache_guard = None;
    }

    /// Loads the Cedar environment from cache or database if expired.
    async fn get_cedar_environment(
        &self,
    ) -> Result<(Arc<PolicySet>, Arc<Entities>)> {
        // Fast path: check cache with a read lock.
        {
            let cache_guard = self.cache.read().await;
            if let Some(cache) = &*cache_guard &&
                cache.expires_at > Instant::now()
            {
                return Ok((
                    Arc::clone(&cache.policy_set),
                    Arc::clone(&cache.entities),
                ));
            }
        }

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
        let mut cedar_entities = Vec::with_capacity(graph_nodes.len());

        for node in graph_nodes {
            let type_name = EntityTypeName::from_str(&node.entity_type)?;
            let entity_id = EntityId::from_str(&node.entity_id)?;
            let uid = EntityUid::from_type_name_and_id(type_name, entity_id);

            let mut parents = HashSet::with_capacity(node.parents.len());
            for parent_ref in node.parents {
                let p_type =
                    EntityTypeName::from_str(&parent_ref.entity_type)?;
                let p_id = EntityId::from_str(&parent_ref.entity_id)?;
                parents.insert(EntityUid::from_type_name_and_id(p_type, p_id));
            }

            let entity = Entity::new(uid, HashMap::new(), parents)?;
            cedar_entities.push(entity);
        }

        let entities = Entities::from_entities(cedar_entities, None)?;

        let arc_policy = Arc::new(policy_set);
        let arc_entities = Arc::new(entities);

        let mut cache_guard = self.cache.write().await;
        *cache_guard = Some(AuthCache {
            policy_set: Arc::clone(&arc_policy),
            entities: Arc::clone(&arc_entities),
            expires_at: Instant::now() + self.cache_ttl,
        });

        Ok((arc_policy, arc_entities))
    }

    /// Evaluates if a user (principal) can perform an action on a specific
    /// resource.
    pub async fn is_authorized(
        &self,
        user_id: &str,
        action: Action,
        resource_name: &str,
    ) -> Result<bool> {
        let (policy_set, entities) = self.get_cedar_environment().await?;

        let user_type = EntityTypeName::from_str("User")?;
        let user_entity_id = EntityId::from_str(user_id)?;
        let principal =
            EntityUid::from_type_name_and_id(user_type, user_entity_id);

        let action_uid = action.action_uid()?;

        let sink_type = EntityTypeName::from_str("Sink")?;
        let sink_entity_id = EntityId::from_str(resource_name)?;
        let resource =
            EntityUid::from_type_name_and_id(sink_type, sink_entity_id);

        let request = Request::new(
            principal,
            action_uid,
            resource,
            CedarContext::empty(),
            None,
        )?;

        let authorizer = Authorizer::new();

        Ok(authorizer
            .is_authorized(&request, &policy_set, &entities)
            .decision() ==
            cedar_policy::Decision::Allow)
    }

    /// Evaluates authorization for multiple resources in bulk.
    pub async fn filter_authorized_resources(
        &self,
        user_id: &str,
        action: Action,
        resource_names: &[String],
    ) -> Result<HashSet<String>> {
        let (policy_set, entities) = self.get_cedar_environment().await?;

        let user_type = EntityTypeName::from_str("User")?;
        let user_entity_id = EntityId::from_str(user_id)?;
        let principal =
            EntityUid::from_type_name_and_id(user_type, user_entity_id);

        let action_uid = action.action_uid()?;
        let sink_type = EntityTypeName::from_str("Sink")?;

        let authorizer = Authorizer::new();
        let mut allowed_resources =
            HashSet::with_capacity(resource_names.len());

        for name in resource_names {
            let sink_entity_id = EntityId::from_str(name)?;
            let resource = EntityUid::from_type_name_and_id(
                sink_type.clone(),
                sink_entity_id,
            );

            let request = Request::new(
                principal.clone(),
                action_uid.clone(),
                resource,
                CedarContext::empty(),
                None,
            )?;

            if authorizer
                .is_authorized(&request, &policy_set, &entities)
                .decision() ==
                cedar_policy::Decision::Allow
            {
                allowed_resources.insert(name.clone());
            }
        }

        Ok(allowed_resources)
    }
}
