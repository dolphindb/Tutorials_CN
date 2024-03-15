# 用新服务器从零开始部署 DolphinDB

本文主要介绍在新服务器部署 DolphinDB 时需要注意哪些系统配置，以及如何选择 DolphinDB 部署方式以符合业务需求。合适的系统配置可以提高 DolphinDB 系统的稳定性和可维护性，而合适的部署方式可以提高业务执行的效率。

- [1. 操作系统配置](#1-操作系统配置)
  - [1.1 平台要求与推荐](#11-平台要求与推荐)
  - [1.2 文件系统与 inode 数量](#12-文件系统与-inode-数量)
  - [1.3 挂载新硬盘](#13-挂载新硬盘)
  - [1.4 开启 core dump](#14-开启-core-dump)
  - [1.5 增大文件最大打开数量](#15-增大文件最大打开数量)
  - [1.6 NTPD](#16-ntpd)
  - [1.7 防火墙配置](#17-防火墙配置)
  - [1.8 Swap](#18-swap)
- [2. 部署 DolphinDB](#2-部署-dolphindb)
  - [2.1 单节点、单机集群、多机集群的选择](#21-单节点单机集群多机集群的选择)
  - [2.2 Docker 和非 Docker 环境运行的选择](#22-docker-和非-docker-环境运行的选择)
  - [2.3 生产环境配置参数实践](#23-生产环境配置参数实践)
  - [2.4 部署流程](#24-部署流程)
  - [2.5 启动流程](#25-启动流程)
- [3. 附件](#3-附件)

## 1. 操作系统配置

本文以 CentOS 7.9.2009 为例，介绍 DolphinDB 相关的系统配置方法。

### 1.1 平台要求与推荐

#### 1.1.1 支持的平台 <!-- omit in toc -->

<table>
    <thead>
        <tr>
            <th>平台</th>
            <th>处理器架构</th>
            <th>是否支持</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan=3>Linux</td>
            <td>x86</td>
            <td>是</td>
        </tr>
        <tr>
            <td>arm</td>
            <td>是</td>
        </tr>
        <tr>
            <td>龙芯</td>
            <td>是</td>
        </tr>
        <tr>
            <td>Windows</td>
            <td>x86</td>
            <td>是</td>
        </tr>
        <tr>
            <td>Mac</td>
            <td>-</td>
            <td>否</td>
        </tr>
        <tr>
            <td>BSD</td>
            <td>-</td>
            <td>否</td>
        </tr>
    </tbody>
</table>

> 在 Linux 系统使用 DolphinDB 要求内核版本为 Linux 2.6.19 或以上，推荐使用 **CentOS 7 稳定版**。
>
> 若使用 Ubuntu 系统：
> 
> (1) 需要在系统安装时在 Storage configuration 中选择 /home 目录的格式为 xfs，以方便后续将 /home 目录格式化为 xfs 文件系统；
> 
> (2) Ubuntu 系统使用 ufw 防火墙，关闭防火墙命令为 `sudo ufw disable`，其他命令请参考 `man ufw`；
> 
> (3) Ubuntu 系统使用 apport 处理 core dump，若需要自定义 core dump，需要禁用 apport，命令为 `sudo systemctl disable apport.service`

#### 1.1.2 依赖软件 <!-- omit in toc -->

DolphinDB 依赖 gcc 4.8.5 或以上版本。以在 CentOS 7 稳定版上安装为例：

```console
# yum install -y gcc
```

#### 1.1.3 推荐硬件配置 <!-- omit in toc -->

需要为 DolphinDB 元数据，redo log 以及数据实体配置不同的硬盘，以优化系统性能。

- **元数据和 redo log**：建议配一块小容量 SSD；若对可靠性要求较高，建议配置两块 SSD 做 RAID1；
    
- **数据实体**：如果无需节约成本，优先考虑多块 SSD 以获得较好的读写性能；如果需要节约成本，优先考虑配置多块机械硬盘以实现并行读写，提高读写吞吐量。
    

> 硬盘容量取决于实际业务。
> 
> 数据实体存在 1 块 SSD 或多块 HDD 的读写性能差距取决于实际情况。

### 1.2 文件系统与 inode 数量

#### 1.2.1 文件系统说明 <!-- omit in toc -->

**推荐**：在 Linux 下推荐使用 xfs 文件系统类型，因为 xfs 文件系统不仅支持硬链接，还支持动态调整 [inode](https://en.wikipedia.org/wiki/Inode) 数量。在 DolphinDB 运行期间，若可用的 inode 不足，将导致 DolphinDB 无法写入数据，可以通过动态增加 inode 数量解决此类问题。

**不推荐**：不支持硬链接的文件系统类型，例如 beegfs。其相较于支持硬链接的系统，其数据更新的性能较差。

root 用户（或有 root 权限的用户，下文命令前面添加 sudo）通过 SSH 连接到全新安装的 CentOS 服务器。首先使用 `df -T` 命令查看文件系统类型：

```console
# df -T
文件系统                类型        1K-块    已用     可用 已用% 挂载点
devtmpfs                devtmpfs  3992420       0  3992420    0% /dev
tmpfs                   tmpfs     4004356       0  4004356    0% /dev/shm
tmpfs                   tmpfs     4004356    8748  3995608    1% /run
tmpfs                   tmpfs     4004356       0  4004356    0% /sys/fs/cgroup
/dev/mapper/centos-root xfs      52403200 1598912 50804288    4% /
/dev/sda1               xfs       1038336  153388   884948   15% /boot
tmpfs                   tmpfs      800872       0   800872    0% /run/user/0
/dev/mapper/centos-home xfs      42970624   33004 42937620    1% /home
```

/home 目录对应的文件系统类型为 xfs，因此可以将 DolphinDB 数据文件目录配置在该目录下。

> 注意：只强烈推荐数据文件目录的文件系统为 xfs，DolphinDB 安装目录、元数据目录、日志目录的文件系统可以为 ext4 等其他文件系统。

若 /home 目录文件系统类型为 ext4 等不支持动态调整 inode 数量的类型，需要将其格式化为 xfs 类型。格式化步骤如下：

1. 备份 /home 数据
    

```console
# cd /
# cp -R /home /tmp
```

2. 卸载 /home 并删除对应逻辑卷

```console
# umount /home
# lvremove /dev/mapper/centos-home
Do you really want to remove active logical volume centos/home? [y/n]: y
  Logical volume "home" successfully removed
```

3. 查看硬盘剩余可用空间

```console
# vgdisplay | grep Free
  Free  PE / Size       10527 / 41.12 GiB # 剩余可用空间为 41.12 GB
```

4. 新建 /home 逻辑卷并格式化为 xfs

```console
# lvcreate -L 41G -n home centos # 根据剩余可用空间填写创建大小
WARNING: xfs signature detected on /dev/centos/home at offset 0. Wipe it? [y/n]: y
  Wiping xfs signature on /dev/centos/home.
  Logical volume "home" created.
# mkfs.xfs /dev/mapper/centos-home
```

5. 挂载 /home 并恢复数据

```console
# mount /dev/mapper/centos-home /home
# mv /tmp/home/* /home/
# chown owner /home/owner # 重新赋予 home 目录文件的权限给对应 owner，需要根据用户名自行修改
```

#### 1.2.2 xfs 文件系统动态调整 inode 数量 <!-- omit in toc -->

若使用 DolphinDB 时出现磁盘空间足够，但因没有可用 inode 导致无法写入文件，可通过增加 inode 数量解决问题，步骤如下：

1. 查看 inode 信息：
    

```console
# xfs_info /dev/mapper/centos-home | grep imaxpct
data = bsize=4096 blocks=10747904, imaxpct=25 # 即 /dev/mapper/centos-home 的 25% 的空间用于存放 inode
# df -i | grep /dev/mapper/centos-home
文件系统                    Inode 已用(I)  可用(I) 已用(I)% 挂载点
/dev/mapper/centos-home 21495808       7 21495801       1% /home
```

可见配置了 /dev/mapper/centos-home 卷下的 25 % 的空间用于存放 inode，当前可用 inode 数为 21495801 个。

2. 增加 inode 数量：

```console
# xfs_growfs -m 30 /dev/mapper/centos-home
meta-data=/dev/mapper/centos-home isize=512    agcount=4, agsize=2686976 blks
         =                       sectsz=512   attr=2, projid32bit=1
         =                       crc=1        finobt=0 spinodes=0
data     =                       bsize=4096   blocks=10747904, imaxpct=25
         =                       sunit=0      swidth=0 blks
naming   =version 2              bsize=4096   ascii-ci=0 ftype=1
log      =internal               bsize=4096   blocks=5248, version=2
         =                       sectsz=512   sunit=0 blks, lazy-count=1
realtime =none                   extsz=4096   blocks=0, rtextents=0
inode max percent changed from 25 to 30
```

3. 再次查看 inode 信息

```console
# df -i | grep /dev/mapper/centos-home
/dev/mapper/centos-home 25794944       7 25794937       1% /home
```

可见当前可用 inode 数增加到了 25794937 个。

#### 1.2.3 ext 文件系统设定合适的 inode 数量 <!-- omit in toc -->

如果必须使用 ext4 等不支持动态调整 inode 数量的文件系统类型，则需要在格式化硬盘时预估文件使用情况和增长速度以设定合适的 inode 数量。例如通过 `mkfs.ext4` 命令的 `-N` 选项指定 inode 数量。尤其当硬盘空间特别大时，ext4 文件系统默认的 inode 数量往往相对较少，建议设置较大的值。

### 1.3 挂载新硬盘

硬盘 IO 性能提升对于大数据处理非常重要，推荐硬件配置见 1.1.3 推荐硬件配置。

物理安装新硬盘或通过云服务商增加新硬盘后，通过 SSH 连接到 CentOS 服务器。本节通过虚拟机添加容量为 50G 的新硬盘，步骤如下：

1. 使用 `fdisk -l` 查看硬盘信息：
    

```console
# fdisk -l
...

磁盘 /dev/sdb：53.7 GB, 53687091200 字节，104857600 个扇区
Units = 扇区 of 1 * 512 = 512 bytes
扇区大小(逻辑/物理)：512 字节 / 512 字节
I/O 大小(最小/最佳)：512 字节 / 512 字节

...
```

可见 /dev/sdb 为新加的 50G 硬盘。

2. 使用 fdisk 程序对新硬盘进行分区：

```console
# fdisk /dev/sdb
欢迎使用 fdisk (util-linux 2.23.2)。

更改将停留在内存中，直到您决定将更改写入磁盘。
使用写入命令前请三思。

Device does not contain a recognized partition table
使用磁盘标识符 0x7becd49e 创建新的 DOS 磁盘标签。

命令(输入 m 获取帮助)：n  # 添加新分区
Partition type:
   p   primary (0 primary, 0 extended, 4 free)
   e   extended
Select (default p): p
分区号 (1-4，默认 1)：
起始 扇区 (2048-104857599，默认为 2048)：
将使用默认值 2048
Last 扇区, +扇区 or +size{K,M,G} (2048-104857599，默认为 104857599)：
将使用默认值 104857599
分区 1 已设置为 Linux 类型，大小设为 50 GiB

命令(输入 m 获取帮助)：q
```

3. 使用 `mkfs.xfs` 命令格式化新硬盘为 xfs 文件系统类型：

```console
# mkfs.xfs /dev/sdb
meta-data=/dev/sdb               isize=512    agcount=4, agsize=3276800 blks
         =                       sectsz=512   attr=2, projid32bit=1
         =                       crc=1        finobt=0, sparse=0
data     =                       bsize=4096   blocks=13107200, imaxpct=25
         =                       sunit=0      swidth=0 blks
naming   =version 2              bsize=4096   ascii-ci=0 ftype=1
log      =internal log           bsize=4096   blocks=6400, version=2
         =                       sectsz=512   sunit=0 blks, lazy-count=1
realtime =none                   extsz=4096   blocks=0, rtextents=0
```

4. 创建挂载点并挂载

```console
# mkdir -p /mnt/dev1
# mount /dev/sdb /mnt/dev1
```

5. 查看新硬盘挂载情况

```console
# df -Th
文件系统                类型      容量  已用  可用 已用% 挂载点
devtmpfs                devtmpfs  3.9G     0  3.9G    0% /dev
tmpfs                   tmpfs     3.9G     0  3.9G    0% /dev/shm
tmpfs                   tmpfs     3.9G  8.6M  3.9G    1% /run
tmpfs                   tmpfs     3.9G     0  3.9G    0% /sys/fs/cgroup
/dev/mapper/centos-root xfs        50G  1.6G   49G    4% /
/dev/sda1               xfs      1014M  150M  865M   15% /boot
/dev/mapper/centos-home xfs        41G   33M   41G    1% /home
tmpfs                   tmpfs     783M     0  783M    0% /run/user/0
/dev/sdb                xfs        50G   33M   50G    1% /mnt/dev1
```

6. 设置开机自动挂载

```console
# blkid /dev/sdb
/dev/sdb: UUID="29ecb452-6454-4288-bda9-23cebcf9c755" TYPE="xfs"
# vi /etc/fstab
UUID=29ecb452-6454-4288-bda9-23cebcf9c755 /mnt/dev1             xfs     defaults        0 0
```

注意这里使用了 UUID 来标识新硬盘，避免了磁盘更换位置导致识别出错。

### 1.4 开启 core dump

[core dump](https://en.wikipedia.org/wiki/Core_dump) 指当程序出错而异常中断时，操作系统会把程序工作的当前状态存储成一个 core 文件。core 文件可以帮助技术支持人员定位问题。因此，在空间足够的情况下，建议开启 core dump。开启步骤如下：

1. 创建存放 core 文件的路径
    

```console
# mkdir /var/crash # 可自行修改存放目录
```

> 注意：
> 
> 为目录预留足以存放若干 core 文件的空间，其中 core 文件最大约为 maxMemSize 配置项的值；
> 
> 确保 DolphinDB 在该目录具备写权限。

2. 设置开启 core dump

```console
# vi /etc/security/limits.conf
* soft core unlimited
```

\* 指为所有用户开启，也可以指定用户名只为 DolphinDB 用户开启，unlimited 指 core 文件大小无限制。

3. 设置 core 文件输出路径与格式

```console
# vi /etc/sysctl.conf
kernel.core_pattern = /var/crash/core-%e-%s-%u-%g-%p-%t
```

格式说明：

- %e – 程序执行文件名

- %s – 生成 core 文件时收到的信号

- %u – 进程用户 ID

- %p – 进程号

- %g – 进程用户组 ID

- %t – 生成 core 文件的时间戳

- %h – 主机名
    

4. 重启后查看是否生效

```console
# ulimit -c
unlimited
```

配置完毕后，建议启动 dolphindb 单节点验证 core dump 配置是否生效，步骤如下：

```console
$ cd /path_to_dolphindb
$ chmod +x ./startSingle.sh
$ ./startSingle.sh
$ kill -11 dolphindb_pid
$ ls /var/crash/ | grep dolphindb_pid # 检查目录下是否有对应core文件
```

### 1.5 增大文件最大打开数量

DolphinDB 运行时同时打开的文件数量可能会大于 CentOS 7 的文件最大打开数量默认值 1024 个，建议配置文件最大打开数量为 102400 个。配置步骤如下：

1. 查看文件最大打开数量
    

```console
# ulimit -n # 用户级
1024
# cat /proc/sys/fs/file-max # 系统级
763964
```

可见用户级文件最大打开数量为 1024 个，系统级为 763964 个。DolphinDB 为用户级，修改用户级文件最大打开数量为 102400 个即可。

2. 修改用户级文件最大打开数量

```console
# vi /etc/security/limits.conf
* soft nofile 102400
* hard nofile 102400
```

\* 指对所有用户生效，也可以配置为指定用户名只对 DolphinDB 用户生效。

3. 若系统级最大打开文件数量的配置值小于 102400 个，需要修改为不小于 102400 的值：

```console
# vi /etc/sysctl.conf
fs.file-max = 102400
```

本文例子中系统级文件最大打开数量为 763964 个，大于 102400 个，故不做修改。

4. 重启后查看配置是否生效

```console
# ulimit -n # 用户级
102400
# cat /proc/sys/fs/file-max # 系统级
763964
```

### 1.6 NTPD

若部署多机集群模式，需要配置 NTPD（Network Time Protocol Daemon）进行时间同步，以确保事务发生的先后顺序正确。本文使用两台虚拟机分别配置为 NTPD 服务端和客户端，配置如下：


| 虚拟机名称 | IP           | 子网掩码      | NTPD 配置                           |
| ---------- | ------------ | ------------- | ----------------------------------- |
| 虚拟机 1    | 192.168.0.30 | 255.255.254.0 | 服务端，与 cn.pool.ntp.org 时间同步 |
| 虚拟机 2    | 192.168.0.31 | 255.255.254.0 | 客户端，与 192.168.0.30 时间同步    |

配置步骤如下：

1. 分别在两台虚拟机上安装 ntpd
    

```console
# yum install ntp
```

2. 在虚拟机 1 上配置与 [cn.pool.ntp.org](http://cn.pool.ntp.org) 时间同步

```console
# vi /etc/ntp.conf
...
# Hosts on local network are less restricted.
restrict 192.168.0.0 mask 255.255.254.0 nomodify notrap

# Use public servers from the pool.ntp.org project.
# Please consider joining the pool (http://www.pool.ntp.org/join.html).
server 0.cn.pool.ntp.org iburst
server 1.cn.pool.ntp.org iburst
server 2.cn.pool.ntp.org iburst
server 3.cn.pool.ntp.org iburst
...
```

其中第 4 行配置 IP 网段在 192.168.0.0 且子网掩码为 255.255.254.0 的本地网络请求本机的 NTP 服务，nomodify 指客户端不能修改服务端的参数配置，notrap 指不提供 trap 远程登录。

3. 在虚拟机 1 上配置防火墙，添加 ntp 服务

```console
# firewall-cmd --add-service=ntp --permanent
# firewall-cmd --reload
```

4. 在虚拟机 2 上配置与虚拟机 1 时间同步

```console
# vi /etc/ntp.conf
...
# Use public servers from the pool.ntp.org project.
# Please consider joining the pool (http://www.pool.ntp.org/join.html).
server 192.168.0.30 iburst
# server 0.centos.pool.ntp.org iburst
# server 1.centos.pool.ntp.org iburst
# server 2.centos.pool.ntp.org iburst
# server 3.centos.pool.ntp.org iburst
...
```

5. 分别在两台虚拟机上启动 ntpd

```console
# systemctl enable ntpd
# systemctl restart ntpd
```

6. 等待若干秒后，查看 ntpd 运行状况

虚拟机 1：

```console
# ntpstat
synchronised to NTP server (202.112.31.197) at stratum 2
   time correct to within 41 ms
   polling server every 64 s
```

虚拟机 2：

```console
# ntpstat
synchronised to NTP server (192.168.0.30) at stratum 3
   time correct to within 243 ms
   polling server every 64 s
```

### 1.7 防火墙配置

运行 DolphinDB 前，需要配置防火墙开放 DolphinDB 的各个节点的端口，或者关闭防火墙。

具体开放哪些端口取决于集群配置，以开放 8900 ~ 8903 TCP 端口为例：

```console
# firewall-cmd --add-port=8900-8903/tcp --permanent
# firewall-cmd --reload
# systemctl restart firewalld
```

若不需要防火墙，可通过如下命令关闭：

```console
# systemctl stop firewalld
# systemctl disable firewalld.service
```

### 1.8 Swap

Swap 即交换分区，在物理内存不够用时，操作系统会从物理内存中把部分暂时不被使用的数据转移到交换分区，从而为当前运行的程序留出足够的物理内存空间，保证程序的正常运行，但会造成系统性能下降。如果系统物理内存充足，且用户比较重视性能，建议关闭 Swap，步骤如下：

1. 检查 Swap 是否已关闭
    

```console
# free -h
              total        used        free      shared  buff/cache   available
Mem:           7.6G        378M        7.1G        8.5M        136M        7.1G
Swap:          7.9G          0B        7.9G
```

可见 Swap 的 total 值为 7.9G，未关闭。

2. 临时关闭 Swap

```console
# swapoff -a
```

3. 再次检查 Swap 是否已关闭

```console
# free -h
              total        used        free      shared  buff/cache   available
Mem:           7.6G        378M        7.1G        8.5M        136M        7.1G
Swap:            0B          0B          0B
```

可见 Swap 的 total 值为 0B，已关闭。

4. 永久关闭 Swap，注释掉第 2 列值为 swap 的行

```console
# vi /etc/fstab
...
# /dev/mapper/centos-swap swap                    swap    defaults        0 0
...
```

## 2. 部署 DolphinDB

系统配置好后，即可根据业务需求选择合适的部署方式部署 DolphinDB。

### 2.1 单节点、单机集群、多机集群的选择

本节介绍不同部署方式之间的比较重要的差异，不同部署方式的功能和应用场景的完整列表见[《DolphinDB 安装使用指南》第 2.4 节](https://gitee.com/dolphindb/Tutorials_CN/blob/master/dolphindb_user_guide.md#24-%E5%8A%9F%E8%83%BD%E5%8F%8A%E5%BA%94%E7%94%A8%E5%9C%BA%E6%99%AF)。

#### 2.1.1 相同单机资源，部署单节点和单机集群的差异 <!-- omit in toc -->

单节点指在单机上部署一个 DolphinDB 单机节点，单机集群指在单机上部署多个 DolphinDB 分布式节点。

单节点部署更简单，且在单机配置（CPU 核数、内存容量、硬盘个数）不高、计算任务不复杂的情况下，单节点的部署方式减少了节点间的网络传输，在性能方面反而比单机集群更好（但并不明显）。

单机集群通常适合密集型计算场景，将计算任务分发到不同的节点（进程）上，可以有效的隔离内存资源竞争，提高计算效率。

集群与单节点的另外两个差异，一是集群支持横向扩展，即支持在线加入新的数据节点，提高整个集群的最大负载；二是集群支持高可用，容错率更高。

综上，单机部署时，建议部署集群模式。

#### 2.1.2 相同节点的情况下，部署单机集群和多机集群的差异 <!-- omit in toc -->

多机集群部署指将 DolphinDB 分布式节点分别部署到多台机器上。

多机可以充分利用各个节点（机器）的计算资源和存储资源。但是节点间通信引入了网络开销，故建议部署在内网并配置万兆网络以降低网络开销。

另外，假设每台机器故障概率相同，多机比单机更容易出现故障，但由于节点分布在多机上，通过开启高可用支持，多机集群容错率更高。

#### 2.1.3 单机多硬盘与多机部署的差异 <!-- omit in toc -->

对于大吞吐量、低计算的任务来说，单机多硬盘集群模式因网络开销小而具有更好的性能。对于小吞吐量、重计算的场景，多机集群的分布式计算优势更明显。

元数据和 redo log 的存储，相关配置项包括：

- [chunkMetaDir](https://docs.dolphindb.cn/zh/db_distr_comp/cfg/cfg_para_ref.html?hl=chunkmetadir#configparamref__section_ckn_54d_syb): 元数据目录
    
- [dfsMetaDir](https://docs.dolphindb.cn/zh/db_distr_comp/cfg/cfg_para_ref.html#configparamref__section_bkn_54d_syb): 该目录保存控制器节点上的分布式文件系统的元数据
    
- [redoLogDir](https://docs.dolphindb.cn/zh/db_distr_comp/cfg/cfg_para_ref.html#configparamref__section_tjn_54d_syb): OLAP 存储引擎重做日志（redo log）的目录
    
- [TSDBRedoLogDir](https://docs.dolphindb.cn/zh/db_distr_comp/cfg/cfg_para_ref.html#configparamref__section_tjn_54d_syb): TSDB 存储引擎重做日志（redo log）的目录
    

这些配置项建议指定到 SSD 以提高读写性能。

数据实体的存储，相关配置项包括：

- [volumes](https://docs.dolphindb.cn/zh/db_distr_comp/cfg/cfg_para_ref.html#configparamref__section_qkn_54d_syb): 数据文件目录。多个目录用 ',' 隔开，例如： /hdd/hdd1/volumes,/hdd/hdd2/volumes,/hdd/hdd3/volumes
    
- [diskIOConcurrencyLevel](https://docs.dolphindb.cn/zh/db_distr_comp/cfg/cfg_para_ref.html#configparamref__section_qkn_54d_syb): 读写磁盘数据的线程数，默认为 1，若 volumes 全部配置为 HDD 硬盘，建议 diskIOConcurrencyLevel 设置为同 HDD 硬盘个数相同的值
    

### 2.2 Docker 和非 Docker 环境运行的选择

Docker 只是轻量化的资源隔离，DolphinDB 部署在 Docker 环境和非 Docker 环境下的运行性能差异不明显，可根据业务需求选择合适的运行环境。

### 2.3 生产环境配置参数实践

以搭建元数据和流数据高可用集群为例介绍如何配置集群各节点。设集群机器硬件配置相同，集群机器信息如下：


| 名称     | IP              | 备注                            |
| -------- | --------------- | ------------------------------- |
| centos-1 | 175.178.100.3   | 1 控制节点，1 代理节点，1 数据节点 |
| centos-2 | 119.91.229.229  | 1 控制节点，1 代理节点，1 数据节点 |
| centos-3 | 175.178.100.213 | 1 控制节点，1 代理节点，1 数据节点 |

3 台机器上 cluster.nodes 与 cluster.cfg 配置文件内容均相同，而 controller.cfg 和 agent.cfg 需要根据机器 IP 和端口号做相应配置。注意下面只列出部分重要配置。

- [**cluster.nodes**](script/deploy_dolphindb_on_new_server/cluster.nodes)

- [**cluster.cfg**](script/deploy_dolphindb_on_new_server/cluster.cfg)

```console
diskIOConcurrencyLevel=0
node1.volumes=/ssd1/dolphindb/volumes/node1,/ssd2/dolphindb/volumes/node1 
node1.redoLogDir=/ssd1/dolphindb/redoLog/node1 
node1.chunkMetaDir=/ssd1/dolphindb/metaDir/chunkMeta/node1 
node1.TSDBRedoLogDir=/ssd1/dolphindb/tsdb/node1/redoLog
chunkCacheEngineMemSize=2
TSDBCacheEngineSize=2
...
```

- [**controller.cfg**](script/deploy_dolphindb_on_new_server/controller.cfg)

```console
localSite=175.178.100.3:8990:controller1
dfsMetaDir=/ssd1/dolphindb/metaDir/dfsMeta/controller1
dfsMetaDir=/ssd1/dolphindb/metaDir/dfsMeta/controller1
dataSync=1
...
```

- [**agent.cfg**](script/deploy_dolphindb_on_new_server/agent.cfg)

```console
localSite=175.178.100.3:8960:agent1
sites=175.178.100.3:8960:agent1:agent,175.178.100.3:8990:controller1:controller,119.91.229.229:8990:controller2:controller,175.178.100.213:8990:controller3:controller
...
```

关于如何配置部分重要配置参数，见下表：

<table>
    <thead>
        <tr>
            <th>文件</th>
            <th>配置参数</th>
            <th>说明</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>cluster.cfg</td>
            <td>node1.volumes=/ssd1/dolphindb/volumes/node1,/ssd2/dolphindb/volumes/node1</td>
            <td>配置多个 SSD 硬盘达到并发读写，以提高读写性能。</td>
        </tr>
        <tr>
            <td>cluster.cfg</td>
            <td>diskIOConcurrencyLevel=0</td>
            <td>合理设置该参数，可以优化读写性能。建议配置如下：若 volumes 配置了 SSD 硬盘，建议设置 diskIOConcurrencyLevel = 0；若 volumes 全部配置为 HDD 硬盘，建议 diskIOConcurrencyLevel 设置为同 HDD 硬盘个数相同的值。</td>
        </tr>
        <tr>
            <td>cluster.cfg</td>
            <td>chunkCacheEngineMemSize=2<br>TSDBCacheEngineSize=2</td>
            <td rowspan=2>DolphinDB 目前要求 cache engine 和 redo log 必须搭配使用。若在 cluster.cfg 配置了 chunkCacheEngineMemSize 和 TSDBCacheEngineSize（即启动 cache engine）则必须在 controller.cfg 里配置 dataSync=1。</td>
        </tr>
        <tr>
            <td>controller.cfg</td>
            <td>dataSync=1</td>
        </tr>
    </tbody>
</table>

### 2.4 部署流程

DolphinDB 为各种部署方式提供了详细的教程，在决定部署方式和配置后，根据教程部署即可，本文涉及的部署方式教程链接如下：

- [单节点部署](https://gitee.com/dolphindb/Tutorials_CN/blob/master/standalone_server.md)
    
- [单节点部署 (嵌入式 ARM 版本)](https://gitee.com/dolphindb/Tutorials_CN/blob/master/ARM_standalone_deploy.md)
    
- [单服务器集群部署](https://gitee.com/dolphindb/Tutorials_CN/blob/master/single_machine_cluster_deploy.md)
    
- [多服务器集群部署](https://gitee.com/dolphindb/Tutorials_CN/blob/master/multi_machine_cluster_deployment.md)
    
- [高可用集群部署教程](https://gitee.com/dolphindb/Tutorials_CN/blob/master/ha_cluster_deployment.md)
    
- [如何扩展集群节点和存储](https://gitee.com/dolphindb/Tutorials_CN/blob/master/scale_out_cluster.md)
    
- [DolphinDB Docker 单机部署方案](https://gitee.com/dolphindb/dolphindb-k8s/blob/master/docker_single_deployment.md)
    
- [基于 Docker-Compose 的 DolphinDB 多容器集群部署](https://gitee.com/dolphindb/dolphindb-k8s/blob/master/docker-compose_high_cluster.md)
    
> 注意：在 windows 系统下部署时，部署路径不能包含中文。

更多教程可以前往[官方教程仓库](https://gitee.com/dolphindb/Tutorials_CN)查看。

### 2.5 启动流程

以启动 2.3 节配置的高可用集群为例，将 2.3 节的配置文件相应放在 centos-1、centos-2、centos-3 机器的 DolphinDB 安装目录/clusterDemo/config 目录下。

> 注意：启动脚本使用了相对路径，故需要到脚本所在目录执行。

#### 2.5.1 启动控制节点 <!-- omit in toc -->

分别在 centos-1、centos-2、centos-3 机器上执行如下命令：

```console
$ cd DolphinDB/clusterDemo/
$ ./startController.sh
```

#### 2.5.2 启动代理节点 <!-- omit in toc -->

分别在 centos-1、centos-2、centos-3 机器上执行如下命令：

```console
$ cd DolphinDB/clusterDemo/
$ ./startAgent.sh
```

#### 2.5.3 启动数据节点 <!-- omit in toc -->

进入任意一个控制节点的 web 集群管理界面，如 [http://175.178.100.3:8990](http://175.178.100.3:8990)，会自动跳转到 leader 节点的集群管理界面。在节点列表选中所有数据节点，点击启动按钮启动即可。web 集群管理界面具体介绍见[Web 集群管理器](https://docs.dolphindb.cn/zh/db_distr_comp/db_man/web/intro.html)。

## 3. 附件

- [cluster.nodes](script/deploy_dolphindb_on_new_server/cluster.nodes)
- [cluster.cfg](script/deploy_dolphindb_on_new_server/cluster.cfg)
- [controller.cfg](script/deploy_dolphindb_on_new_server/controller.cfg)
- [agent.cfg](script/deploy_dolphindb_on_new_server/agent.cfg)