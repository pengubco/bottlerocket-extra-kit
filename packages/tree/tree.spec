Name:    %{_cross_os}tree
Version: 2.3.2
Release: 1%{?dist}
Summary: List contents of directories in a tree-like format
License: GPL-2.0-or-later
URL:     https://oldmanprogrammer.net/source.php?dir=projects/tree

Source0: https://oldmanprogrammer.net/tar/tree/tree-%{version}.tgz

BuildRequires: %{_cross_os}glibc-devel

%description
%{summary}.

%prep
%autosetup -n tree-%{version} -p1

%build
# tree ships a hand-written Makefile with no configure script. Assigning
# CFLAGS/CPPFLAGS on the command line overrides the Makefile's own "+=" lines,
# so the flags tree needs (-std=c11, large-file defines) are repeated here.
%make_build \
    CC="%{_cross_target}-gcc" \
    CFLAGS="%{_cross_cflags} -std=c11" \
    CPPFLAGS="-DLARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64" \
    LDFLAGS="%{_cross_ldflags}"

%install
install -d %{buildroot}%{_cross_bindir}
install -p -m 0755 tree %{buildroot}%{_cross_bindir}/tree

%files
%license LICENSE
%{_cross_attribution_file}
%{_cross_bindir}/tree

%changelog
* Sun Sep 28 2026 Bottlerocket Team <bottlerocket@amazon.com> - 2.3.2-1
- Initial package for tree 2.3.2
