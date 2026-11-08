Name:		mockito
Version:	5.24.0
Release:	1
Summary:	Mocking framework for Java tests
Group:		Development/Java
License:	MIT AND Apache-2.0
URL:		https://site.mockito.org/
Source0:	https://codeload.github.com/mockito/mockito/tar.gz/refs/tags/v%{version}#/mockito-%{version}.tar.gz
BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	python
BuildRequires:	sysjar
BuildRequires:	mvn(net.bytebuddy:byte-buddy)
BuildRequires:	mvn(net.bytebuddy:byte-buddy-agent)
BuildRequires:	mvn(org.ow2.asm:asm)
BuildRequires:	mvn(org.ow2.asm:asm-commons)
BuildRequires:	mvn(org.objenesis:objenesis)
BuildRequires:	mvn(junit:junit)
BuildRequires:	mvn(org.hamcrest:hamcrest)
BuildRequires:	mvn(org.opentest4j:opentest4j)
BuildRequires:	mvn(org.jspecify:jspecify)
Obsoletes:	mockito-junit-jupiter < %{version}-%{release}

%description
Mockito creates test doubles with a short API. This package is the core
library, built against the system Byte Buddy and ASM. The inline mock
maker is the default. The JUnit Jupiter integration is not included.
Copied equality and weak-map code retains its Apache-2.0 terms.

%prep
%setup -q -n mockito-%{version}
find . -name '*.class' -delete
find . -name '*.jar' -delete
if find . \( -name '*.class' -o -name '*.jar' \) | grep -q .; then
	echo "prebuilt bytecode remains" >&2
	exit 1
fi
find mockito-core/src/main/java -name '*.java' -print0 \
	| xargs -0 sed -i 's/net\.bytebuddy\.jar\.asm/org.objectweb.asm/g'
if grep -R -q 'net\.bytebuddy\.jar\.asm' mockito-core/src/main/java; then
	echo "shaded ASM import remains" >&2
	exit 1
fi

%build
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java}"
CP=/usr/share/java/byte-buddy.jar
CP=$CP:/usr/share/java/byte-buddy-agent.jar
CP=$CP:/usr/share/java/objenesis.jar
CP=$CP:/usr/share/java/junit.jar
CP=$CP:/usr/share/java/hamcrest/hamcrest.jar
CP=$CP:/usr/share/java/opentest4j/opentest4j.jar
CP=$CP:/usr/share/java/jspecify.jar
CP=$CP:/usr/share/java/asm.jar
mkdir -p build/classes
find mockito-core/src/main/java -name '*.java' ! -name 'module-info.java' \
	| sort > build/sources.list
python - << 'PY'
from pathlib import Path
lines = Path("build/sources.list").read_text().splitlines()
if len(lines) != 482:
    raise SystemExit("source count " + str(len(lines)))
if any(line.endswith("module-info.java") for line in lines):
    raise SystemExit("module-info was listed")
module = Path("mockito-core/src/main/java/module-info.java")
if not module.is_file():
    raise SystemExit("module-info.java missing")
PY
"$JAVA_HOME/bin/javac" --release 11 -encoding UTF-8 -cp "$CP" \
	-d build/classes @build/sources.list
python - << 'PY'
from pathlib import Path
root = Path("build/classes")
count = 0
for path in root.rglob("*.class"):
    data = path.read_bytes()
    major = int.from_bytes(data[6:8], "big")
    if major != 55:
        raise SystemExit(str(path) + " has major " + str(major))
    if b"net/bytebuddy/jar/" in data:
        raise SystemExit(str(path) + " still references shaded ASM")
    count += 1
if count != 587:
    raise SystemExit("class count " + str(count))
dispatcher = root / "org/mockito/internal/creation/bytebuddy/inject/MockMethodDispatcher.class"
if not dispatcher.is_file():
    raise SystemExit("dispatcher class missing")
PY
rm -rf build/jar-root
mkdir -p build/jar-root
cp -a build/classes/. build/jar-root/
install -D \
	build/classes/org/mockito/internal/creation/bytebuddy/inject/MockMethodDispatcher.class \
	build/jar-root/org/mockito/internal/creation/bytebuddy/inject-MockMethodDispatcher.raw
rm -rf build/jar-root/org/mockito/internal/creation/bytebuddy/inject
cp mockito-core/src/main/java/org/mockito/internal/matchers/apachecommons/commons-lang-license.txt \
	build/commons-lang-license.txt
cp mockito-core/src/main/java/org/mockito/internal/util/concurrent/LICENSE \
	build/weak-lock-free-LICENSE
cat > build/manifest.mf << 'EOF'
Manifest-Version: 1.0
Premain-Class: org.mockito.internal.PremainAttach
Can-Retransform-Classes: true
Automatic-Module-Name: org.mockito
Implementation-Version: %{version}

EOF
"$JAVA_HOME/bin/jar" --create --manifest build/manifest.mf \
	--file build/mockito.jar -C build/jar-root .
cat > build/mockito.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.mockito</groupId>
  <artifactId>mockito-core</artifactId>
  <version>%{version}</version>
  <name>mockito-core</name>
  <description>Mockito core built against the system Byte Buddy and ASM.</description>
  <url>https://site.mockito.org/</url>
  <licenses>
    <license>
      <name>MIT</name>
      <url>https://opensource.org/licenses/MIT</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>net.bytebuddy</groupId>
      <artifactId>byte-buddy</artifactId>
      <version>1.18.17</version>
    </dependency>
    <dependency>
      <groupId>net.bytebuddy</groupId>
      <artifactId>byte-buddy-agent</artifactId>
      <version>1.18.17</version>
    </dependency>
    <dependency>
      <groupId>org.ow2.asm</groupId>
      <artifactId>asm</artifactId>
      <version>9.11.1</version>
    </dependency>
    <dependency>
      <groupId>org.objenesis</groupId>
      <artifactId>objenesis</artifactId>
      <version>3.6</version>
      <scope>runtime</scope>
    </dependency>
    <dependency>
      <groupId>junit</groupId>
      <artifactId>junit</artifactId>
      <version>4.13.2</version>
      <scope>provided</scope>
      <optional>true</optional>
    </dependency>
    <dependency>
      <groupId>org.hamcrest</groupId>
      <artifactId>hamcrest</artifactId>
      <version>3.0</version>
      <scope>provided</scope>
      <optional>true</optional>
    </dependency>
    <dependency>
      <groupId>org.opentest4j</groupId>
      <artifactId>opentest4j</artifactId>
      <version>1.3.0</version>
      <scope>provided</scope>
      <optional>true</optional>
    </dependency>
    <dependency>
      <groupId>org.jspecify</groupId>
      <artifactId>jspecify</artifactId>
      <version>1.0.0</version>
      <scope>provided</scope>
      <optional>true</optional>
    </dependency>
  </dependencies>
</project>
EOF

%install
sysjar install --buildroot %{buildroot} \
	--artifact build/mockito.pom:build/mockito.jar \
	--file-name mockito \
	--filelist .mfiles

%check
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java}"
CP=/usr/share/java/byte-buddy.jar
CP=$CP:/usr/share/java/byte-buddy-agent.jar
CP=$CP:/usr/share/java/objenesis.jar
CP=$CP:/usr/share/java/asm.jar
CP=$CP:/usr/share/java/asm-commons.jar
"$JAVA_HOME/bin/jar" tf build/mockito.jar > build/jar-list.txt
for class in \
	org/mockito/Mockito.class \
	org/mockito/internal/PremainAttach.class \
	org/mockito/internal/creation/bytebuddy/inject-MockMethodDispatcher.raw
do
	if ! grep -F -x -q "$class" build/jar-list.txt; then
		echo "missing $class" >&2
		exit 1
	fi
done
if grep -E 'bytebuddy/inject/|module-info|net/bytebuddy/jar/' build/jar-list.txt; then
	echo "jar contains the inject package, module-info, or shaded ASM" >&2
	exit 1
fi
python - << 'PY'
from pathlib import Path
import zipfile
jar = zipfile.ZipFile("build/mockito.jar")
text = jar.read("META-INF/MANIFEST.MF").decode()
for line in (
    "Premain-Class: org.mockito.internal.PremainAttach",
    "Can-Retransform-Classes: true",
    "Automatic-Module-Name: org.mockito",
):
    if line not in text:
        raise SystemExit("manifest missing " + line)
PY
"$JAVA_HOME/bin/jar" --describe-module --file build/mockito.jar > build/module.txt
if ! grep -F -q 'org.mockito automatic' build/module.txt; then
	echo "automatic module name" >&2
	exit 1
fi
mkdir -p build/probe
cat > build/Probe.java << 'EOF'
import org.mockito.Mockito;

public class Probe {
	interface Foo {
		String bar();
	}

	static class Box {
		private final int n;

		Box(int n) {
			this.n = n;
		}

		int n() {
			return n;
		}
	}

	public static void main(String[] args) {
		Foo foo = Mockito.mock(Foo.class);
		Mockito.when(foo.bar()).thenReturn("ok");
		if (!"ok".equals(foo.bar())) {
			throw new AssertionError("interface stub failed");
		}
		Box box = Mockito.mock(Box.class);
		Mockito.when(box.n()).thenReturn(7);
		if (box.n() != 7) {
			throw new AssertionError("class stub failed");
		}
		System.out.println("probe ok");
	}
}
EOF
"$JAVA_HOME/bin/javac" --release 11 -encoding UTF-8 \
	-cp "build/mockito.jar:$CP" -d build/probe build/Probe.java
# install() on Java 21+ self-attaches through a helper JVM. ABF isolates
# /proc in a pid namespace, so that helper cannot see the target. Loading
# this jar with -javaagent runs PremainAttach first, and the inline mock
# maker reuses that instrumentation.
"$JAVA_HOME/bin/java" -javaagent:build/mockito.jar \
	--enable-native-access=ALL-UNNAMED \
	-cp "build/probe:build/mockito.jar:$CP" \
	Probe > build/probe.out
if ! grep -F -x -q 'probe ok' build/probe.out; then
	echo "probe failed" >&2
	exit 1
fi

%files -f .mfiles
%license LICENSE
%license build/commons-lang-license.txt
%license build/weak-lock-free-LICENSE
%doc README.md
