use std::fs;
use std::path::PathBuf;
use std::process::{exit, Command};

fn main() -> Result<(), std::io::Error> {
    // Get the package directory
    let package_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let vendor_tarball = package_dir.join("nerdctl-2.1.6-vendor.tar.gz");

    // Check if vendor tarball exists
    if !vendor_tarball.exists() {
        eprintln!("Vendor tarball not found, creating it...");
        let script_path = package_dir.join("create-vendor-tarball.sh");
        
        let output = Command::new("bash")
            .arg(&script_path)
            .current_dir(&package_dir)
            .output()?;
        
        if !output.status.success() {
            eprintln!("Failed to create vendor tarball");
            eprintln!("stdout: {}", String::from_utf8_lossy(&output.stdout));
            eprintln!("stderr: {}", String::from_utf8_lossy(&output.stderr));
            exit(1);
        }
        
        // Verify the tarball was created
        if !vendor_tarball.exists() {
            eprintln!("Vendor tarball was not created successfully");
            exit(1);
        }
        
        // Extract the SHA512 from the script output
        let output_str = String::from_utf8_lossy(&output.stdout);
        if let Some(sha_line) = output_str.lines().find(|line| line.contains("SHA512:")) {
            if let Some(sha512) = sha_line.split("SHA512:").nth(1) {
                let sha512 = sha512.trim();
                eprintln!("Updating Cargo.toml with new SHA512: {}", sha512);
                
                // Update Cargo.toml with the new hash
                let cargo_toml_path = package_dir.join("Cargo.toml");
                let cargo_toml = fs::read_to_string(&cargo_toml_path)?;
                
                // Find the vendor tarball entry and update its sha512
                let lines: Vec<&str> = cargo_toml.lines().collect();
                let mut updated_lines = Vec::new();
                let mut in_vendor_section = false;
                
                for line in lines {
                    if line.contains(r#"url = "file://nerdctl-2.1.6-vendor.tar.gz""#) {
                        in_vendor_section = true;
                        updated_lines.push(line.to_string());
                    } else if in_vendor_section && line.contains("sha512 = ") {
                        updated_lines.push(format!(r#"sha512 = "{}""#, sha512));
                        in_vendor_section = false;
                    } else {
                        updated_lines.push(line.to_string());
                    }
                }
                
                fs::write(&cargo_toml_path, updated_lines.join("\n") + "\n")?;
                eprintln!("Cargo.toml updated successfully");
                
                // Tell cargo to rerun if Cargo.toml changes
                println!("cargo:rerun-if-changed=Cargo.toml");
            }
        }
        
        eprintln!("Vendor tarball created successfully");
    }

    // Now run the standard buildsys build-package
    let ret = Command::new("buildsys").arg("build-package").status()?;
    if !ret.success() {
        exit(1);
    }
    Ok(())
}
