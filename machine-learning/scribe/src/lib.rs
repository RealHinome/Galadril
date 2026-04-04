//! Galadril Scribe.

pub mod engine;
pub mod tools;

pub use engine::{Scribe, ScribeConfig};
pub use tools::add_section::Section;
pub use tools::database::{DatabaseProvider, NoOpProvider};
