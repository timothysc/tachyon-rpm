%global commit      9d66149f791f57103d3d78ac48e36343d4fa2b9c
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global shortname   tachyon

Name:          amplab-%{shortname}
# Given the naming conflicts with other packages, and eventually this will 
# switch to apache-tachyon should 
Version:       0.4.0
Release:       3.%{shortcommit}%{?dist}
Summary:       Reliable File Sharing at Memory Speed Across Cluster Frameworks
License:       BSD
URL:           https://github.com/amplab/tachyon/wiki
Source0:       https://github.com/timothysc/tachyon/archive/%{commit}/%{shortname}-%{version}-%{shortcommit}.tar.gz
Source1:       %{shortname}-tmpfiles.conf
Source2:       %{shortname}-master.service
Source3:       %{shortname}-slave.service
Source4:       %{shortname}-layout.sh
Source5:       %{shortname}-env.sh

Patch0:        log4props.patch

BuildRequires: java-devel
BuildRequires: mvn(commons-io:commons-io)
BuildRequires: mvn(log4j:log4j)
BuildRequires: mvn(org.apache.ant:ant)
BuildRequires: mvn(org.apache.commons:commons-lang3)

BuildRequires: mvn(org.apache.hadoop:hadoop-common)
BuildRequires: mvn(org.apache.hadoop:hadoop-mapreduce-client-core)
BuildRequires: mvn(org.apache.hadoop:hadoop-hdfs)
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
BuildRequires: systemd

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
avoids going to disk to load data-sets that
are frequently read.

%package javadoc
Summary:       Javadoc for %{name}

%description javadoc
This package contains javadoc for %{name}.

%prep
%setup -q -n tachyon-%{commit}
find -name '*.class' -print -delete
find -name '*.jar' -print -delete

%patch0 -p1

sed -i "s|<artifactId>hadoop-client|<artifactId>hadoop-mapreduce-client-core|" pom.xml

%pom_xpath_remove "pom:repositories"

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
 
%mvn_file org.tachyonproject:%{shortname} %{shortname}
%mvn_build

%install
%mvn_install

#######################
# install system integration files
#######################
mkdir -p %{buildroot}%{_sysconfdir}/tmpfiles.d
install -m 0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/tmpfiles.d/%{shortname}.conf

#######################
mkdir -p %{buildroot}%{_unitdir}
install -m 0644 %{SOURCE2} %{SOURCE3} %{buildroot}%{_unitdir}/

#######################
mkdir -p %{buildroot}%{_libexecdir}/
install -m 0755 %{SOURCE4} %{buildroot}%{_libexecdir}/
install -m 0755 libexec/* %{buildroot}%{_libexecdir}/

#######################
mkdir -p %{buildroot}%{_bindir}/
install -m 0755 bin/tachyon* %{buildroot}%{_bindir}/

#######################
mkdir -p %{buildroot}/%{_sysconfdir}/%{shortname}
install -m 0644 conf/log4j.properties conf/slaves %{buildroot}/%{_sysconfdir}/%{shortname}
install -m 0644 %{SOURCE5} %{buildroot}/%{_sysconfdir}/%{shortname}

#######################
mkdir -p -m0755 %{buildroot}/%{_var}/log/%{shortname}
mkdir -p -m0755 %{buildroot}%{_var}/lib/%{shortname}/journal

%files -f .mfiles
%doc LICENSE README.md
%dir %_sysconfdir/%{shortname}
%config(noreplace) %_sysconfdir/%{shortname}/log4j.properties
%config(noreplace) %_sysconfdir/%{shortname}/slaves
%config(noreplace) %_sysconfdir/%{shortname}/tachyon-env.sh
%config(noreplace) %_sysconfdir/tmpfiles.d/%{shortname}.conf
%{_bindir}/tachyon*
%{_libexecdir}/tachyon*
%config(noreplace) %_sysconfdir/tmpfiles.d/%{shortname}.conf
%{_unitdir}/*
%attr(0755,tachyon,tachyon) %dir %{_var}/log/%{shortname}
%attr(0755,tachyon,tachyon) %dir %{_var}/lib/%{shortname}/journal

%files javadoc -f .mfiles-javadoc
%doc LICENSE

############################################
%pre
getent group tachyon >/dev/null || groupadd -f -r tachyon
if ! getent passwd tachyon >/dev/null ; then
      useradd -r -g tachyon -d %{_sharedstatedir}/%{shortname} -s /sbin/nologin \
              -c "%{shortname} daemon account" tachyon
fi
exit 0

%post
%systemd_post %{shortname}-master.service %{shortname}-slave.service

%preun
%systemd_preun %{shortname}-slave.service %{shortname}-master.service

%postun
%systemd_postun_with_restart %{shortname}-slave.service %{shortname}-master.service

%changelog
* Thu Nov 7 2013 Timothy St. Clair<tstclair@redhat.com> 0.4.0-3.9d66149
- Modifications from system testing.

* Mon Nov 4 2013 Timothy St. Clair<tstclair@redhat.com> 0.4.0-2
- System integration and testing.

* Mon Oct 28 2013 Timothy St. Clair <tstclair@redhat.com> 0.4.0-1
- Pre-release update to 0.4.0 with script modifications.

* Thu Oct 10 2013 Timothy St. Clair <tstclair@redhat.com> 0.3.0-1
- Update to the latest in preparation for release. 

* Sun Sep 29 2013 gil cattaneo <puntogil@libero.it> 0.2.1-1
- initial rpm
