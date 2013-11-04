%global commit      ace4347470c74caeb6977a9b5decf7fb61422a4e
%global shortcommit %(c=%{commit}; echo ${c:0:7})

Name:          tachyon
Version:       0.4.0
Release:       1.%{shortcommit}%{?dist}
Summary:       Reliable File Sharing at Memory Speed Across Cluster Frameworks
License:       BSD
URL:           https://github.com/amplab/tachyon/wiki
Source0:       https://github.com/timothysc/tachyon/archive/%{commit}/%{name}-%{version}-%{shortcommit}.tar.gz
Source1:       %{name}-tmpfiles.conf
Source2:       %{name}-master.service
Source3:       %{name}-slave.service
Source4:       %{name}-layout.sh

BuildRequires: java-devel
BuildRequires: mvn(commons-io:commons-io)
#BuildRequires: mvn(de.javakaffee:kryo-serializers)
BuildRequires: mvn(log4j:log4j)
BuildRequires: mvn(org.apache.ant:ant)
BuildRequires: mvn(org.apache.commons:commons-lang3)

BuildRequires: mvn(org.apache.hadoop:hadoop-common)
BuildRequires: mvn(org.apache.hadoop:hadoop-mapreduce-client-core)
BuildRequires: mvn(org.apache.curator:curator-recipes)
BuildRequires: mvn(org.apache.curator:curator-test)
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
BuildRequires: maven-plugin-bundle
BuildRequires: exec-maven-plugin
BuildRequires: maven-remote-resources-plugin
BuildRequires: maven-site-plugin
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
%setup -q -n %{name}-%{commit}
find -name '*.class' -print -delete
find -name '*.jar' -print -delete

sed -i "s|<artifactId>hadoop-client|<artifactId>hadoop-mapreduce-client-core|" pom.xml

# Remove unnecessary plugin
%pom_remove_plugin :maven-assembly-plugin

# Fix unavailable jetty-jsp-2.1
%pom_remove_dep org.eclipse.jetty:jetty-jsp
%pom_add_dep org.glassfish.web:javax.servlet.jsp::compile

#make additions for hadoop2
%pom_add_dep org.apache.hadoop:hadoop-common
%pom_add_dep org.apache.hadoop:hadoop-hdfs

# Fix jetty9 support
sed -i "s|org.mortbay.log.Log|org.eclipse.jetty.util.log.Log|" src/main/java/tachyon/MasterInfo.java
sed -i "s|Log.info|Log.getRootLogger().info|" src/main/java/tachyon/MasterInfo.java

# This is required to update to the latest thrift.
./bin/thrift-gen.sh

%build
 
%mvn_file org.tachyonproject:%{name} %{name}
%mvn_build

%install
%mvn_install

#######################
mkdir -p %{buildroot}%{_sysconfdir}/tmpfiles.d
install -m 0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/tmpfiles.d/%{name}.conf

#######################
mkdir -p %{buildroot}%{_unitdir}
install -m 0644 %{SOURCE2} %{SOURCE3} %{buildroot}%{_unitdir}/

#######################
mkdir -p %{buildroot}%{_libexecdir}/
install -m 0755 %{SOURCE4} %{buildroot}%{_libexecdir}/

#######################
mkdir -p %{buildroot}%{_bindir}/
install -m 755 bin/tachyo* %{buildroot}%{_bindir}/

%files -f .mfiles
%doc LICENSE README.md
%config(noreplace) %_sysconfdir/tmpfiles.d/%{name}.conf
%{_bindir}/tachyon*
%{_libexecdir}/tachyon*
%config(noreplace) %_sysconfdir/tmpfiles.d/%{name}.conf
%{_unitdir}/*

%files javadoc -f .mfiles-javadoc
%doc LICENSE

############################################
%pre
getent group tachyon >/dev/null || groupadd -f -r tachyon
if ! getent passwd tachyon >/dev/null ; then
      useradd -r -g tachyon -d %{_sharedstatedir}/%{name} -s /sbin/nologin \
              -c "%{name} daemon account" tachyon
fi
exit 0

%post
%systemd_post %{name}-slave.service %{name}-master.service

%preun
%systemd_preun %{name}-slave.service %{name}-master.service

%postun
%systemd_postun_with_restart %{name}-slave.service %{name}-master.service

%changelog
* Mon Oct 28 2013 Timothy St. Clair <tstclair@redhat.com> 0.4.0-1
- Pre-release update to 0.4.0 with script modifications. 

* Thu Oct 10 2013 Timothy St. Clair <tstclair@redhat.com> 0.3.0-1
- Update to the latest in preparation for release. 

* Sun Sep 29 2013 gil cattaneo <puntogil@libero.it> 0.2.1-1
- initial rpm
