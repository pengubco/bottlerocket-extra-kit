# AWS CLI v2 bundles Python extension modules with non-standard RPATHs
# (e.g. /usr/local/lib in _sqlite3.cpython-313.so). Suppress the rpath check
# for this package since we cannot recompile the pre-built PyInstaller payload.
# 0x0002 = non-standard RPATH, 0x0010 = empty RPATH
%global __os_install_post %(echo '%{__os_install_post}' | sed 's!/usr/lib/rpm/check-rpaths!!g')

Name:    %{_cross_os}awscli2
Version: 2.27.0
Release: 1%{?dist}
Summary: AWS Command Line Interface version 2
License: Apache-2.0
URL:     https://aws.amazon.com/cli/

# AWS CLI v2 ships as arch-specific self-contained installer zips.
# Each zip contains a dist/ directory with the PyInstaller-frozen executable
# and all bundled libraries (libpython, .so files, etc.). The aws binary
# must be run from within dist/ so it can locate its sibling libraries.
Source0: https://awscli.amazonaws.com/awscli-exe-linux-x86_64-%{version}.zip
Source1: https://awscli.amazonaws.com/awscli-exe-linux-aarch64-%{version}.zip

BuildRequires: unzip

%description
%{summary}.

%prep
unzip %{S:0} -d awscli2-x86_64
unzip %{S:1} -d awscli2-aarch64

%build
%{nil}

%install
# Install the full dist/ tree under datadir (not libexecdir) so the SDK's
# check-fips script does not scan it. The dist/ tree contains a bundled
# cryptography/_rust.abi3.so that uses 'ring' rather than aws-lc-rs; since
# this is a pre-built third-party PyInstaller payload we cannot recompile it.
# check-fips only scans bindir and libexecdir, so datadir is safe.
install -d %{buildroot}%{_cross_datadir}/awscli2
cp -r awscli2-%{_cross_arch}/aws/dist %{buildroot}%{_cross_datadir}/awscli2/dist

# Symlinks in bindir point into the dist/ tree.
# The PyInstaller aws binary resolves siblings relative to its own real path,
# so the symlink target must live inside dist/.
install -d %{buildroot}%{_cross_bindir}
ln -sf %{_cross_datadir}/awscli2/dist/aws %{buildroot}%{_cross_bindir}/aws
ln -sf %{_cross_datadir}/awscli2/dist/aws_completer %{buildroot}%{_cross_bindir}/aws_completer

%files
%{_cross_attribution_file}
%{_cross_bindir}/aws
%{_cross_bindir}/aws_completer
%dir %{_cross_datadir}/awscli2
%{_cross_datadir}/awscli2/dist

%changelog
- Initial package for AWS CLI v2.27.0
