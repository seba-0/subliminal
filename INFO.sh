# INFO.sh
. /pkgscripts/include/pkg_util.sh
package="subliminal"
version="2.0.5"
maintainer="diaoul/synocommunity/seba"
maintainer_url="http://github.com/seba-0"
displayname="Subliminal"
distributor="seba"
distributor_url="http://github.com/seba-0"
arch="noarch"
firmware="6.0-7312"
report_url="http://github.com/seba-0/subliminal/issues"
dsmuidir="app"
dsmappname="com.seba.subliminal"
thirdparty="yes"
install_dep_packages="PythonModule"
description="Subliminal allows you automatically download best-matching subtitles for your movies and tv shows on your DiskStation. This package is named after Subliminal, the Python library used to search and download subtitles."
description_fre="Subliminal vous permet de télécharger automatiquement les meilleurs sous-titres pour vos films et séries sur votre DiskStation. Ce paquet est nommé d'après Subliminal, la librairie Python utilisée pour rechercher et télécharger les sous-titres."
firmware="$1"
[ "$(caller)" != "0 NULL" ] && return 0
pkg_dump_info
