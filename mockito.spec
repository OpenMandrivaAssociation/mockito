%_javapackages_macros
Name:           mockito
Version:        1.9.0
Release:        13.1%{?dist}
Summary:        A Java mocking framework

License:        MIT
URL:            http://code.google.com/p/mockito/
Source0:        mockito-%{version}.tar.xz
Source1:        make-mockito-sourcetarball.sh
Patch0:         fixup-ant-script.patch
Patch1:         fix-cglib-refs.patch
Patch2:         maven-cglib-dependency.patch
Patch3:         fix-bnd-config.patch
Patch4:         %{name}-matcher.patch

BuildArch:      noarch
BuildRequires:  jpackage-utils
BuildRequires:  java-devel
BuildRequires:  ant
BuildRequires:  objenesis
BuildRequires:  cglib
BuildRequires:  junit4
BuildRequires:  hamcrest
BuildRequires:  aqute-bnd

Requires:       jpackage-utils
Requires:       java
Requires:       objenesis
Requires:       cglib
Requires:       junit4
Requires:       hamcrest

%description
Mockito is a mocking framework that tastes really good. It lets you write
beautiful tests with clean & simple API. Mockito doesn't give you hangover
because the tests are very readable and they produce clean verification
errors.

%package javadoc
Summary:        Javadocs for %{name}

Requires:       jpackage-utils

%description javadoc
This package contains the API documentation for %{name}.

%prep
%setup -q
%patch0 -p1
%patch1 -p1
%patch2 -p1
# Set Bundle-Version properly
sed -i 's/Bundle-Version= ${version}/Bundle-Version= %{version}/' conf/mockito-core.bnd
%patch3
%patch4 -p1

%build
%if 0%{?fedora}
ant jar javadoc
%else
CLASSPATH=$(build-classpath aqute-bnd objenesis) %{ant} jar javadoc
%endif
# Convert to OSGi bundle
pushd target
java -jar $(build-classpath aqute-bnd) wrap -output mockito-core-%{version}.bar -properties ../conf/mockito-core.bnd mockito-core-%{version}.jar
#java -classpath $(build-classpath aqute-bnd objenesis) wrap -output mockito-core-%{version}.bar -properties ../conf/mockito-core.bnd mockito-core-%{version}.jar
popd

%install
mkdir -p $RPM_BUILD_ROOT%{_javadir}
sed -i -e "s|@version@|%{version}|g" maven/mockito-core.pom
cp -p target/mockito-core-%{version}.bar $RPM_BUILD_ROOT%{_javadir}/%{name}.jar

install -d -m 755 $RPM_BUILD_ROOT%{_mavenpomdir}
install -pm 644 maven/mockito-core.pom  \
        $RPM_BUILD_ROOT%{_mavenpomdir}/JPP-%{name}.pom

mkdir -p $RPM_BUILD_ROOT%{_javadocdir}/%{name}
cp -rp target/javadoc/* $RPM_BUILD_ROOT%{_javadocdir}/%{name}

%add_maven_depmap JPP-%{name}.pom %{name}.jar -a "org.mockito:mockito-all"

%files
%{_javadir}/%{name}.jar
%{_mavenpomdir}/JPP-%{name}.pom
%{_mavendepmapfragdir}/%{name}
%doc NOTICE
%doc LICENSE

%files javadoc
%{_javadocdir}/%{name}
%doc LICENSE
%doc NOTICE
