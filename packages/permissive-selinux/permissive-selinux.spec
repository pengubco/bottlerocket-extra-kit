Name: %{_cross_os}permissive-selinux
Summary: Set SELinux mode to permissive
Version: 0.1.0
Release: 1%{?dist}
License: MIT

Source0: permissive-selinux.service
Source1: permissive.cil

%description
%{summary}

%prep
%{nil}

%build
%{nil}

%install
install -D -d %{buildroot}%{_cross_datarootdir}/selinux/modules
install -D -p -m 0644 %{S:0} %{buildroot}%{_cross_unitdir}/permissive-selinux.service
install -m 0755 %{S:1} %{buildroot}%{_cross_datarootdir}/selinux/modules

%files
%{_cross_unitdir}/permissive-selinux.service
%{_cross_datarootdir}/selinux/modules/permissive.cil
%{_cross_attribution_file}
