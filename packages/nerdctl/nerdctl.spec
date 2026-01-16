%global goproject github.com/containerd
%global gorepo nerdctl
%global goimport %{goproject}/%{gorepo}

%global gover 2.1.6
%global rpmver %{gover}

Name: %{_cross_os}nerdctl
Version: %{rpmver}
Release: 1%{?dist}
Summary: Nerdctl
License: Apache-2.0

URL: https://%{goimport}
Source0: https://%{goimport}/archive/refs/tags/v%{version}.tar.gz
Source1: nerdctl-%{version}-vendor.tar.gz
Source1000: clarify.toml

BuildRequires: git
BuildRequires: %{_cross_os}glibc-devel
Requires: %{_cross_os}cni-plugins
Requires: %{name}(binaries)

%description
%{summary}.

%package bin
Summary: Nerdctl
Provides: %{name}(binaries)
Requires: (%{_cross_os}image-feature(no-fips) and %{name})
Conflicts: (%{_cross_os}image-feature(fips) or %{name}-fips-bin)

%description bin
%{summary}.

%package fips-bin
Summary: Nerdctl, FIPS edition
Provides: %{name}(binaries)
Requires: (%{_cross_os}image-feature(fips) and %{name})
Conflicts: (%{_cross_os}image-feature(no-fips) or %{name}-bin)

%description fips-bin
%{summary}.

%prep
%autosetup -Sgit -n %{gorepo}-%{gover} 
%cross_go_setup %{gorepo}-%{gover} %{goproject} %{goimport}

# Extract pre-vendored Go dependencies into the Go workspace
cd GOPATH/src/%{goimport}
tar -xzf %{S:1}

%build
%cross_go_configure %{goimport}

declare -a BUILD_ARGS
BUILD_ARGS=(
  -ldflags="${GOLDFLAGS}"
)

go build "${BUILD_ARGS[@]}" -o nerdctl ./cmd/nerdctl
gofips build "${BUILD_ARGS[@]}" -o fips/nerdctl ./cmd/nerdctl

%install
install -d %{buildroot}%{_cross_bindir}
install -p -m 0755 nerdctl %{buildroot}%{_cross_bindir}

install -d %{buildroot}%{_cross_fips_bindir}
install -p -m 0755 fips/nerdctl %{buildroot}%{_cross_fips_bindir}

%cross_scan_attribution --clarify %{S:1000} go-vendor vendor

%files
%license LICENSE NOTICE
%{_cross_attribution_file}
%{_cross_attribution_vendor_dir}

%files bin
%{_cross_bindir}/nerdctl

%files fips-bin
%{_cross_fips_bindir}/nerdctl

%changelog
* Thu Jan 16 2025 Bottlerocket Team <bottlerocket@amazon.com> - 2.1.6-1
- Initial package for nerdctl v2.1.6
