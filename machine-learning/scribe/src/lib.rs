//! Galadril Scribe.

pub mod engine;
pub mod tools;

pub use engine::{ScribeChat, ScribeConfig};
pub use tools::database::{DatabaseProvider, NoOpProvider};

#[cfg(feature = "latex")]
pub use engine::report::ScribeReport;
#[cfg(feature = "latex")]
pub use tools::add_section::Section;
