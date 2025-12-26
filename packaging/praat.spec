Name:           praat
Version:        6.4.49
Release:        1%{?dist}
Summary:        Speech analysis and synthesis tool for phonetics

License:        GPL-2.0-or-later
URL:            https://www.fon.hum.uva.nl/praat/

Source0:        https://github.com/mwprado/praat-rpm-package/archive/refs/heads/main.zip
Source1:        https://github.com/praat/praat.github.io/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  rsync
BuildRequires:  pkgconfig

BuildRequires:  gtk3-devel
BuildRequires:  pulseaudio-libs-devel
BuildRequires:  alsa-lib-devel
BuildRequires:  pipewire-jack-audio-connection-kit-devel

BuildRequires:  desktop-file-utils
BuildRequires:  hicolor-icon-theme

Recommends:     charis-sil-fonts
Recommends:     doulos-sil-fonts

%description
Praat is a scientific computer program for speech analysis, speech synthesis,
and manipulation of speech sounds. It is widely used in phonetics.

%prep
%autosetup -q -T -c -n %{name}-%{version}

# Source0: packaging tree
unzip -q %{SOURCE0} -d packaging
PACKDIR="$(find packaging -maxdepth 1 -type d -name 'praat-rpm-package-*' | head -n1)"
test -n "$PACKDIR"
ln -snf "$PACKDIR" pkg

# Source1: upstream
tar -xzf %{SOURCE1} -C .
UPDIR="$(find . -maxdepth 1 -type d -name 'praat.github.io-*' | head -n1)"
test -n "$UPDIR"
ln -snf "$UPDIR" upstream

%build
pushd upstream

# Passo obrigatório do HOW_TO_BUILD_ONE (Linux pulse gcc)
cp -f makefiles/makefile.defs.linux.pulse-gcc ./makefile.defs

# Build com paralelismo via macro RPM (não fixa -j15)
%{__make} %{?_smp_mflags}

popd

%install
rm -rf %{buildroot}

# Instala o binário manualmente (upstream geralmente não oferece "make install" consistente)
pushd upstream

PRAAT_BIN=""
for f in ./praat ./bin/praat ./build/praat ./praat_*/praat; do
  if [ -x "$f" ]; then PRAAT_BIN="$f"; break; fi
done
if [ -z "$PRAAT_BIN" ]; then
  PRAAT_BIN="$(find . -maxdepth 3 -type f -name praat -perm -111 2>/dev/null | head -n1)"
fi

if [ -z "$PRAAT_BIN" ]; then
  echo "ERROR: binário 'praat' não encontrado após build."
  exit 1
fi

install -Dpm0755 "$PRAAT_BIN" %{buildroot}%{_bindir}/praat
popd

# Desktop file: prioriza o do Source0 (pkg/), senão gera um mínimo
if [ -f pkg/praat.desktop ]; then
  install -Dpm0644 pkg/praat.desktop %{buildroot}%{_datadir}/applications/praat.desktop
else
  install -Dpm0644 /dev/stdin %{buildroot}%{_datadir}/applications/praat.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Praat
GenericName=Speech analysis
Comment=Doing phonetics by computer
Exec=praat
Icon=praat
Terminal=false
Categories=Science;Education;AudioVideo;Audio;
StartupNotify=true
EOF
fi

# Ícone: prioriza pkg/, senão tenta achar no upstream
ICON_SRC=""
for i in pkg/praat.svg pkg/praat.png pkg/icons/praat.svg pkg/icons/praat.png; do
  if [ -f "$i" ]; then ICON_SRC="$i"; break; fi
done

if [ -z "$ICON_SRC" ]; then
  for i in upstream/praat.png upstream/praat.svg upstream/icons/praat.png upstream/icons/praat.svg \
           upstream/resources/praat.png upstream/resources/praat.svg \
           upstream/pictures/praat.png upstream/pictures/praat.svg; do
    if [ -f "$i" ]; then ICON_SRC="$i"; break; fi
  done
fi

if [ -n "$ICON_SRC" ]; then
  case "$ICON_SRC" in
    *.svg)
      install -Dpm0644 "$ICON_SRC" %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/praat.svg
      ;;
    *.png)
      install -Dpm0644 "$ICON_SRC" %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/praat.png
      ;;
  esac
fi

# Docs (best-effort)
if [ -d upstream/docs ]; then
  mkdir -p %{buildroot}%{_docdir}/%{name}
  cp -a upstream/docs/* %{buildroot}%{_docdir}/%{name}/
fi
if [ -f upstream/README.md ]; then
  mkdir -p %{buildroot}%{_docdir}/%{name}
  cp -a upstream/README.md %{buildroot}%{_docdir}/%{name}/
fi

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/praat.desktop || :

%post
%desktop_database_post
%icon_theme_cache_post

%postun
%desktop_database_postun
%icon_theme_cache_postun

%files
%license upstream/LICENSE* upstream/COPYING* 2>/dev/null
%doc %{_docdir}/%{name} 2>/dev/null
%{_bindir}/praat
%{_datadir}/applications/praat.desktop
%{_datadir}/icons/hicolor/*/apps/praat.* 2>/dev/null

%changelog
* Fri Dec 26 2025 Moacyr Waldemiro Prado Neto <mwprado@users.noreply.github.com> - 6.4.49-1
- Initial RPM packaging (Makefile-only) using Source0 packaging tree + Source1 upstream
- Copy makefile.defs.linux.pulse-gcc before build; use RPM parallel macro

