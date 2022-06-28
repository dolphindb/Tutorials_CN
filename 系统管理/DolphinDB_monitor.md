# 使用Prometheus监控告警

DolphinDB提供了三种方式进行性能监控：
* 使用内置函数,如[`getperf`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getPerf.html),[`getClusterPerf`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getClusterPerf.html)和[`getJobStat`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getJobStat.html)；
* Web界面；
* 通过第三方系统的API，如Prometheus、Grafana等。

前两种方式的使用说明详见[用户手册](https://www.dolphindb.cn/cn/help/SystemManagement/PerformanceMonitoring.html)，本文以使用Prometheus监控DolphinDB为例来详细说明第三种方法。

Prometheus（普罗米修斯）是一款开源的监控和预警工具，起始是由SoundCloud公司开发的。2012年起成为社区开源项目，拥有非常活跃的开发人员和用户社区。为强调开源及独立维护，Prometheus于2016年加入了云原生云计算基金会（CNCF）。在本文中，以监控系统平均负载为例，先安装配置Prometheus和其Alertmanager组件，然后接入邮件报警，演示系统负载高时自动邮件报警的功能。用户可以参照此例，根据自己的实际需求来实现具体的运维方案。


- [使用Prometheus监控告警](#使用prometheus监控告警)
  - [1. Prometheus metrics](#1-prometheus-metrics)
  - [2. 下载Prometheus](#2-下载prometheus)
  - [3.安装及配置](#3安装及配置)
    - [3.1 Prometheus安装及配置](#31-prometheus安装及配置)
    - [3.2 Alertmanager安装及配置](#32-alertmanager安装及配置)
    - [3.3 启动Prometheus和Alertmanager](#33-启动prometheus和alertmanager)

## 1. Prometheus metrics

DolphinDB为需要监控的服务产生相应的metrics（指标），Prometheus Server可以直接使用。目前支持的metrics如下所示：

|指标|	类型|	含义|
|----|----|----|
|cumMsgLatency|	Gauge |累计消息延时|
|lastMsgLatency | Gauge |前一消息延时|
|lastMinuteNetworkRecv |	Gauge |前一分钟网络接收字节数	|
|maxLast10QueryTime  | Gauge |前10个完成的查询执行所耗费时间的最大值	|
|lastMinuteNetworkSend| Gauge |前一分钟网络发送字节数|
|diskWriteRate| Gauge |磁盘写速率|
|networkSendRate| Gauge |网络发送速率|
|memoryUsed| Gauge |	节点使用的内存|
|jobLoad| Gauge |作业负载|
|medLast10QueryTime  | Gauge |前10个完成的查询执行所耗费时间的中间值|
|cpuUsage  | Gauge |CPU使用率|
|memoryAlloc   | Gauge |节点中DolphinDB当前内存池的容量|
|medLast100QueryTime  | Gauge |前100个完成的查询执行所耗费时间的中间值|
|avgLoad |	Gauge |平均负载|
|runningJobs  | Gauge |正在执行中的作业和任务数|
|maxLast100QueryTime |	Gauge |前100个完成的查询执行所耗费时间的最大值|
|networkRecvRate  | Gauge |网络接收速率|
|maxRunningQueryTime | Gauge |当前正在执行的查询的耗费时间的最大值|
|diskCapacity| Gauge |磁盘容量|
|queuedJobs| Gauge |队列中的作业和任务数|
|diskFreeSpace| Gauge |磁盘剩余空间|
|diskReadRate| Gauge |磁盘读速率|
|lastMinuteWriteVolume| Gauge |前一分钟写磁盘容量|
|lastMinuteReadVolume| Gauge |前一分钟读磁盘容量|

注意这些Metrics也可以通过http://ip:port/metrics 来查看。例如，本机单节点，监听在8848端口的DolphinDB，可以通过http://127.0.0.1:8848/metrics 来查看相关数据。

## 2. 下载Prometheus

从Prometheus官网下载Prometheus和Alertmanager，下载链接为：[https://prometheus.io/download/](https://prometheus.io/download/)。相关文档可参阅[官方帮助](https://prometheus.io/docs/prometheus/latest/getting_started/)。

Prometheus监控DolplhinDB，既可以选择在宿主机上部署Prometheus，也可以通过Docker容器来部署运行，甚至通过k8s等工具来进行一些列相关组件的部署。本例的测试环境为安装了Ubuntu 16.04 LTS的台式机，
官网上Prometheus最新为2.26.0版本，Alertmanager最新为0.21.0版本。因此从官网下载最新的Prometheus[二进制包](https://github.com/prometheus/prometheus/releases/download/v2.26.0/prometheus-2.26.0.linux-amd64.tar.gz) 和Alertmanager[二进制包](https://github.com/prometheus/alertmanager/releases/download/v0.21.0/alertmanager-0.21.0.linux-amd64.tar.gz)。 

## 3.安装及配置

### 3.1 Prometheus安装及配置

* 解压缩安装包

解压缩之后，目录文件如下所示:
```
demo@zhiyu:~/prometheus-2.26.0.linux-amd64$ ls
console_libraries  consoles  data  LICENSE  NOTICE  prometheus  prometheus.yml  promtool
```
* 修改prometheus.yml

其中,上述目录下的prometheus.yml就是配置文件，修改后配置如下:
```
global:
  scrape_interval:     15s 
  evaluation_interval: 15s

alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - 127.0.0.1:9093

rule_files:
  - "./avgLoadMonitor.yml"

scrape_configs:
  - job_name: 'DolphinDB'
    static_configs:
    - targets: ['115.239.209.122:8080','115.239.209.122:25667']
```

其中，alerting部分的targets部分，指向了后面需要启动的Alertmanager的地址。
rule_files部分，是一些预警的规则定义，这里的avgLoadMonitor.yml,将在后面配置Alertmanager时创建。scrape_configs部分的targets里，则是待监控的DolphinDB的节点地址，本例中添加了2个DolphinDB节点，若有更多节点时，可以继续按IP:PORT这样的格式在这里添加。

* 创建avgLoadMonitor.yml文件

配置avgLoadMonitor.yml的内容如下所示:
```
groups:
- name: avgLoadMonitor
  rules:
  - alert: avgLoadMonitor
    expr: avgLoad > 0.1
    for: 15s
    labels:
      severity: 1
      team: node
    annotations:
      summary: "{{ $labels.instance }} avgLoad larger than 0.1!"

```
其中，报警规则是avgLoad > 0.1。avgLoad是DolphinDB提供的一个指标。DolphinDB支持的的指标如上一节所示，若需要，也可以根据实际情况替换成其它指标和报警条件。


### 3.2 Alertmanager安装及配置

* 解压缩安装包

解压后，目录文件如下所示:
```
demo@zhiyu:~/alertmanager-0.21.0.linux-amd64$ ls
alertmanager  alertmanager.yml  amtool  LICENSE  NOTICE
```
其中，alertmanager.yml是配置文件。其中，主要定义报警的通知渠道(邮件，钉钉，企业微信等)。这样，当Prometheus那边预警规则被触发时，会根据其配置文件中的alerting部分，推送到Alertmanager服务这里。然后Alertmanager根据其配置的渠道，进行报警消息推送。

* 配置alertmanager.yml

这里演示邮件推送，修改alertmanager.yml如下:
```
global:
  resolve_timeout: 5m
  smtp_from: 'xxxx@qq.com'
  smtp_smarthost: 'smtp.qq.com:465'
  smtp_auth_username: 'xxxx@qq.com'
  smtp_auth_password: 'yyyy'
  smtp_require_tls: false
  smtp_hello: 'qq.com'

route:
  group_by: ['alertname']
  group_wait: 5s
  group_interval: 5s
  repeat_interval: 5m
  receiver: 'email'
receivers:
- name: 'email'
  email_configs:
  - to: 'xxxx@qq.com'
    send_resolved: true
inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']

```

>注：本例中，xxxx@qq.com请替换为实际邮箱地址；
> 邮箱需要开启STMP功能，然后配置中的smtp_auth_password这个配置项，这个并不是邮箱的密码，这里为第三方登录邮箱的授权码。以qq邮箱为例，获取授权码的步骤如下：
第一步：登录邮箱后，先点击下图中的`设置`,然后点击`账户`；

![qq1](../images/monitor/setting.png?raw=true)

第二步：拖到账户web页面的页尾，点击`开启`以启动SMTP服务；

![qq2](../images/monitor/startsmtp.png?raw=true)

第三步：按照弹出的对话框，发短信；

![qq3](../images/monitor/sms.png?raw=true)

第四步：在上图中点击`我已发送`;即可得到如下所示授权码。

![qq4](../images/monitor/code.png?raw=true)

### 3.3 启动Prometheus和Alertmanager

* 启动Prometheus命令如下：
```
demo@zhiyu:~/prometheus-2.26.0.linux-amd64$ nohup ./prometheus --config.file=promethes.yml &
```

默认地，prometheus绑定在9090端口，可以通过前端Web来访问，本例的是127.0.0.1:9090


* 启动Alertmanager命令如下：

```
demo@zhiyu:~/alertmanager-0.21.0.linux-amd64$ nohup ./alertmanager --config.file=alertmanager.yml &
```
AlertManger默认绑定在9093端口，前端地址是http://127.0.0.1:9093 里面可以看到Prometheus里触发报警规则推送过来的信息，在这里会交给具体的渠道处理，从而实现报警。本例中，当负载超过0.1是，邮箱里就会收到邮件提醒。

启动后，到此就完成DolphinDB的指标监控和报警了。Prometheus内置了一个简单的Web控制台，可以查询指标，查看配置信息或者Service Discovery等，例如：

访问http://127.0.0.1:9090/targets 可以看到被监控的节点：

![targets](../images/monitor/targets.png?raw=true)

访问http://127.0.0.1:9090/rules 可以看到监控报警规则：

![targets](../images/monitor/rules.png?raw=true)

访问http://127.0.0.1:9090/graph 在输入框中输入指标如lastMinuteNetworkRecv，可以看到各指标的图形展示：

![targets](../images/monitor/graph.png?raw=true)


实际工作中，查看指标或者创建仪表盘通常使用Grafana，Prometheus作为Grafana的数据源；另外，DolphinDB 已经实现了Grafana的服务端和客户端的接口，具体配置可以参考[grafana教程](https://gitee.com/dolphindb/grafana-datasource)。