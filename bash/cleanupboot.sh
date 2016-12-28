# !/bin/bash
### auto-remove old linux images (which are probably just taking up space)
dpkg --get-selections|grep 'linux-image*'|awk '{print $1}'|egrep -v "linux-image-$(uname -r)|linux-image-generic" |while read n;do apt-get -y remove $n;done
apt-get autoremove -y
exit
