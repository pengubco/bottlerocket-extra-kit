Name:    %{_cross_os}golang
Version: 1.26.1
Release: 1%{?dist}
Summary: The Go programming language toolchain
License: BSD-3-Clause
URL:     https://go.dev

# Official Go binary tarballs for each architecture.
Source0: https://dl.google.com/go/go%{version}.linux-amd64.tar.gz
Source1: https://dl.google.com/go/go%{version}.linux-arm64.tar.gz

%description
%{summary}.

%prep
%ifarch x86_64
tar -xzf %{S:0}
%endif
%ifarch aarch64
tar -xzf %{S:1}
%endif

%build
%{nil}

%install
# Install the full Go toolchain under /usr/local/go so GOROOT works out of the box.
install -d %{buildroot}/usr/local
cp -a go %{buildroot}/usr/local/go

# Symlink the go and gofmt binaries into the standard bin directory.
install -d %{buildroot}%{_cross_bindir}
ln -sf /usr/local/go/bin/go %{buildroot}%{_cross_bindir}/go
ln -sf /usr/local/go/bin/gofmt %{buildroot}%{_cross_bindir}/gofmt

%files
%license go/LICENSE
%{_cross_attribution_file}
/usr/local/go
%{_cross_bindir}/go
%{_cross_bindir}/gofmt

%changelog
* Fri Mar 06 2026 Bottlerocket Team <bottlerocket@amazon.com> - 1.26.1-1
- Initial package for Go 1.26.1
