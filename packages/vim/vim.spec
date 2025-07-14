	
Summary: The VIM editor
URL:     http://www.vim.org/
Name:    %{_cross_os}vim
Version: 9.1.0
Release: 1%{?dist}
License: Vim AND LGPL-2.1-or-later AND MIT AND GPL-1.0-only AND (GPL-2.0-only OR Vim) AND Apache-2.0 AND BSD-2-Clause AND BSD-3-Clause AND GPL-2.0-or-later AND GPL-3.0-or-later AND OPUBL-1.0 AND Apache-2.0 WITH Swift-exception

Source0: https://github.com/vim/vim/archive/v%{version}.tar.gz

# Disable debugsource package for tiny vim build
%global debug_package %{nil}

%define vimdir vim91
	
BuildRequires: %{_cross_os}glibc-devel
BuildRequires: %{_cross_os}libacl-devel
BuildRequires: %{_cross_os}libattr-devel
BuildRequires: %{_cross_os}libcap-devel
BuildRequires: %{_cross_os}libncurses-devel
BuildRequires: %{_cross_os}libselinux-devel
BuildRequires: %{_cross_os}libxcrypt-devel
BuildRequires: %{_cross_os}readline-devel
BuildRequires: autoconf
BuildRequires: gcc

Requires: %{_cross_os}libstdc++
Requires: %{_cross_os}libacl
Requires: %{_cross_os}libattr
Requires: %{_cross_os}libcap
Requires: %{_cross_os}libncurses
Requires: %{_cross_os}libselinux
Requires: %{_cross_os}libxcrypt
Requires: %{_cross_os}readline
 
%description
%{summary}.
 
%prep
%autosetup -n vim-%{version} -p1

%build
export CC="%{_cross_target}-gcc" 

cd src
autoconf

%cross_configure \
    --with-features=tiny \
    --without-x \
    --disable-gui \
    --disable-nls \
    --disable-netbeans \
    --enable-selinux \
    --enable-acl \
    --disable-pythoninterp \
    --disable-perlinterp \
    --disable-tclinterp \
    --with-tlib=tinfo \
    vim_cv_tgetent=yes \
    vim_cv_terminfo=yes \
    vim_cv_getcwd_broken=no \
    vim_cv_timer_create=yes \
    vim_cv_stat_ignores_slash=no \
    vim_cv_memmove_handles_overlap=yes \
    vim_cv_toupper_broken=no

%make_build CC="${CC}" 

%install
%make_install
 
%files 
%{_cross_bindir}/*
%{_cross_datadir}/vim/%{vimdir}
%exclude %{_cross_datadir}/applications/*.desktop
%exclude %{_cross_datadir}/icons
%exclude %{_cross_mandir}
%{_cross_attribution_file}
