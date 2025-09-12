# Bottlerocket Extra Kit
This is a kit for building [Bottlerocket](https://github.com/bottlerocket-os). It contains RPM packages used for debugging on Bottlerocket that are not included in the [bottlerocket-kernel-kit](https://github.com/bottlerocket-os/bottlerocket-kernel-kit) and [bottlerocket-core-kit](https://github.com/bottlerocket-os/bottlerocket-core-kit). 

## Use RPM package from the kit
Take the [aws-dev](https://github.com/bottlerocket-os/bottlerocket/tree/develop/variants/aws-dev) variant as an example. 

Step 1. Add vendor and kit to the {project-root}/Twoliter.toml.
```toml
[vendor.peng]
registry = "public.ecr.aws/m8c0s8v8"

[[kit]]
name = "bottlerocket-extra-kit"
version = "0.0.3-kernalkit-4.3.0-corekit-10.3.0-sdk-0.64.0"
vendor = "peng" 
```

Step 2. Add packages you need to the included-packages `variants/aws-dev/Cargo.toml`. See [available packages](#packages).
```plain
sysstat
vim
curl
permissive-selinux
```

Step 3. Build Bottlerocket image and AMI as usual.

## bottlerocket-core-kit and bottlerocket-sdk
In building Bottlerocket image, the bottlerocket-kernel-kit, bottlerocket-core-kit and bottlerocket-sdk must be the same
across all kits. Otherwise, you may see errors below.  
```plain
Error: cannot have multiple versions of the same kit (bottlerocket-core-kit-9.2.1@bottlerocket != bottlerocket-core-kit-9.2.0@bottlerocket
```
The extra-kit will release with latest core-kit and sdk at the time of the release. The releases name follows pattern. 
`v0.0.3-kernalkit-4.3.0-corekit-10.3.0-sdk-0.64.0`, which reads: 
- bottlerocket-extra-kit version 0.0.3
- bottlerocket-kernal-kit version 4.3.0
- bottlerocket-core-kit version 10.3.0
- bottlerocket-sdk version 0.64.0

If you need to build with different core-kit adn sdk version, please check out and update the Twoliter.toml.

## Build and publish this kit 
```
make update
make fetch
make build
make publish VENDOR=peng
```

## Packages
- [curl](https://curl.se) v8.12.1.
- [jsoncpp](https://github.com/open-source-parsers/jsoncpp) v1.9.6.
- [oomd](https://github.com/facebookincubator/oomd) v0.5.0.
- [permissive-selinux] Set SELinux mode to permissive. Useful to debug/develop bypassing SELinux denials. For example, 
run a shell script.
- [sysstat](https://github.com/sysstat/sysstat) v12.7.7. Commands: sar, sadf, iostat, mpstat, pidstat, tapestat, cifsiostat
- [vim](https://github.com/vim/vim) v9.1.0.
