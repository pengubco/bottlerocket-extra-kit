use std::process::{exit, Command};

fn main() -> Result<(), std::io::Error> {
    // bpftrace is only available as a pre-built static binary for x86_64.
    // Skip the build silently on aarch64.
    let arch = std::env::var("BUILDSYS_ARCH").unwrap_or_default();
    if arch == "aarch64" {
        println!("cargo:warning=bpftrace: skipping build on aarch64 (no upstream binary available)");
        return Ok(());
    }

    let ret = Command::new("buildsys").arg("build-package").status()?;
    if !ret.success() {
        exit(1);
    }
    Ok(())
}
