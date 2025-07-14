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
version = "0.0.1"
vendor = "peng" 
```

Step 2. Add packages you need to the included-packages `variants/aws-dev/Cargo.toml`. See [available packages](#packages).
```plain
sysstat
vim
curl
```

Step 3. Build Bottlerocket image and AMI as usual.

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
- [sysstat](https://github.com/sysstat/sysstat) v12.7.7. Commands: sar, sadf, iostat, mpstat, pidstat, tapestat, cifsiostat
- [vim](https://github.com/vim/vim) v9.1.0.
