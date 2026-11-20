use std::process::{exit, Command};

fn main() -> Result<(), std::io::Error> {
    // Intel PCM reads Intel x86 model-specific registers and uncore PMUs;
    // upstream does not support aarch64. Skip the build silently there.
    let arch = std::env::var("BUILDSYS_ARCH").unwrap_or_default();
    if arch == "aarch64" {
        println!("cargo:warning=pcm: skipping build on aarch64 (x86_64-only tool)");
        return Ok(());
    }

    let ret = Command::new("buildsys").arg("build-package").status()?;
    if !ret.success() {
        exit(1);
    }
    Ok(())
}
