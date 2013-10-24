Name:          tachyon
Version:       0.3.0
Release:       1%{?dist}
Summary:       Reliable File Sharing at Memory Speed Across Cluster Frameworks
License:       BSD
URL:           https://github.com/amplab/tachyon/wiki
#Source0:       https://github.com/amplab/tachyon/archive/v%{version}.tar.gz
Source0:       v0.3.0.tar.gz
Source1:       generate-tarball.sh

BuildRequires: java-devel
BuildRequires: mvn(commons-io:commons-io)
BuildRequires: mvn(de.javakaffee:kryo-serializers)
BuildRequires: mvn(log4j:log4j)
BuildRequires: mvn(org.apache.ant:ant)
BuildRequires: mvn(org.apache.commons:commons-lang3)

BuildRequires: mvn(org.apache.hadoop:hadoop-common)
BuildRequires: mvn(org.apache.hadoop:hadoop-mapreduce-client-core)

BuildRequires: mvn(org.apache.thrift:libthrift)
BuildRequires: mvn(org.eclipse.jetty:jetty-webapp)
BuildRequires: mvn(org.eclipse.jetty:jetty-server)
BuildRequires: mvn(org.eclipse.jetty:jetty-servlet)
BuildRequires: mvn(org.glassfish.web:javax.servlet.jsp)
BuildRequires: mvn(org.slf4j:slf4j-api)
BuildRequires: mvn(org.slf4j:slf4j-log4j12)

# Test deps
BuildRequires: mvn(junit:junit)

BuildRequires: maven-local
BuildRequires: exec-maven-plugin
BuildRequires: replacer
BuildRequires: thrift

BuildArch:     noarch

%description
Tachyon is a fault tolerant distributed file system
enabling reliable file sharing at memory-speed
across cluster frameworks, such as Spark and MapReduce.
It achieves high performance by leveraging lineage
information and using memory aggressively.
Tachyon caches working set files in memory, and
enables different jobs/queries and frameworks to
access cached files at memory speed. Thus, Tachyon
avoids going to disk to load datasets that
are frequently read.

%package javadoc
Summary:       Javadoc for %{name}

%description javadoc
This package contains javadoc for %{name}.

%prep
%setup -q -n %{name}-%{version}
find -name '*.class' -print -delete
find -name '*.jar' -print -delete

# Use hadoop2 as default profile
%pom_xpath_remove "pom:project/pom:profiles/pom:profile[pom:id = 'hadoop1' ]"
%pom_xpath_remove "pom:project/pom:profiles/pom:profile[pom:id = 'hadoop3' ]"

# Fix hadoop deps aid
sed -i "s|<artifactId>hadoop-core|<artifactId>hadoop-common|" pom.xml
sed -i "s|<artifactId>hadoop-client|<artifactId>hadoop-mapreduce-client-core|" pom.xml

# Remove unnecessary plugin
%pom_remove_plugin :maven-assembly-plugin

# Fix replacer plugin aId
%pom_xpath_set "pom:project/pom:build/pom:plugins/pom:plugin[pom:groupId = 'com.google.code.maven-replacer-plugin' ]/pom:artifactId" replacer

# Fix unavailable jetty-jsp-2.1
%pom_remove_dep org.eclipse.jetty:jetty-jsp-2.1
%pom_add_dep org.glassfish.web:javax.servlet.jsp::compile

# Fix jetty9 support
sed -i "s|org.mortbay.log.Log|org.eclipse.jetty.util.log.Log|" src/main/java/tachyon/MasterInfo.java
sed -i "s|Log.info|Log.getRootLogger().info|" src/main/java/tachyon/MasterInfo.java

# This is required to update to the latest thrift.
./bin/thrift-gen.sh

%build
 
%mvn_file org.tachyonproject:%{name} %{name}
%mvn_build -- -Phadoop2 -X

%install
%mvn_install

%files -f .mfiles
%doc LICENSE README.md
#%{_bindir}/clear-cache.sh

%files javadoc -f .mfiles-javadoc
%doc LICENSE


%changelog
* Thu Oct 10 2013 Timothy St. Clair <tstclair@redhat.com> 0.3.0-1
- Update to the latest in preparation for release. 

* Sun Sep 29 2013 gil cattaneo <puntogil@libero.it> 0.2.1-1
- initial rpm
