use std::process::{exit, Command};

fn main() -> Result<(), std::io::Error> {
    // turbostat reads x86 model-specific registers and is only built by the
    // kernel for x86. Skip the build silently on aarch64.
    let arch = std::env::var("BUILDSYS_ARCH").unwrap_or_default();
    if arch == "aarch64" {
        println!("cargo:warning=turbostat: skipping build on aarch64 (x86-only tool)");
        return Ok(());
    }

    let ret = Command::new("buildsys").arg("build-package").status()?;
    if !ret.success() {
        exit(1);
    }
    Ok(())
}
