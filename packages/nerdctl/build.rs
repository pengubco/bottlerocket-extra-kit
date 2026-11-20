use std::path::PathBuf;
use std::process::{exit, Command};

// The vendor tarball is generated locally (it is not published anywhere), so
// create it on first build. create-vendor-tarball.sh is reproducible, so the
// result must match the sha512 pinned in Cargo.toml; buildsys verifies that.
// This script never edits Cargo.toml: rewriting a tracked file during a build
// would leave the tree dirty and block publishing.
fn main() -> Result<(), std::io::Error> {
    let package_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let vendor_tarball = package_dir.join("nerdctl-2.1.6-vendor.tar.gz");
    println!("cargo:rerun-if-changed=create-vendor-tarball.sh");

    if !vendor_tarball.exists() {
        eprintln!("Vendor tarball not found, creating it...");
        let status = Command::new("bash")
            .arg(package_dir.join("create-vendor-tarball.sh"))
            .current_dir(&package_dir)
            .status()?;
        if !status.success() || !vendor_tarball.exists() {
            eprintln!("Failed to create the vendor tarball");
            exit(1);
        }
    }

    let ret = Command::new("buildsys").arg("build-package").status()?;
    if !ret.success() {
        exit(1);
    }
    Ok(())
}
