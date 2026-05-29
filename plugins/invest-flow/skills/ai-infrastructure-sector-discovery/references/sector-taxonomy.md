# AI 基建板块发现固定种子池

## 使用规则

每周扫描默认从下列固定种子板块开始，再根据最新架构变化、财报、订单、产品路线图和产业新闻动态新增候选板块。固定种子池用于保持周度可比性；动态新增用于捕捉早期变化。

## 固定种子板块

| 板块 | 典型环节 | 代表公司/观察对象 | 默认指标 |
|------|----------|-------------------|----------|
| HBM | HBM3E/HBM4、base die、封装协同 | SK Hynix、Samsung、Micron、TSMC、设备/材料供应商 | HBM bit growth、ASP、产能预订、良率、客户认证、capex |
| CoWoS / SoIC | 先进封装、interposer、hybrid bonding | TSMC、ASE、Amkor、BESI、ASMPT、DISCO | 月产能、扩产节奏、lead time、良率、AI chip 订单 |
| ABF / substrate | ABF 载板、高端 substrate | Unimicron、Ibiden、Shinko、AT&S、Nan Ya PCB | 高端 ABF 利用率、价格、扩产、客户认证 |
| 光模块 / CPO / 硅光 | 800G/1.6T 光模块、LPO、CPO、硅光、laser | Coherent、Lumentum、InnoLight、Eoptolink、Broadcom、Marvell | 速率迁移、出货、ASP、DSP/LPO/CPO 路线、客户认证 |
| 光芯片 / 激光器 | EML、CW laser、VCSEL、PIC | Coherent、Lumentum、II-VI 相关供应链、硅光厂商 | laser 供给、良率、功耗、CPO design-in |
| Switch ASIC / SerDes | 交换芯片、高速 SerDes、retimer | Broadcom、Marvell、Astera Labs、Credo | switch radix、SerDes 速率、端口数、订单、客户平台导入 |
| NIC / DPU | 高速 NIC、SmartNIC、DPU | NVIDIA、Broadcom、Marvell、AMD/Pensando | 网络带宽、attach rate、推理集群部署、软件生态 |
| 铜互联 / 连接器 | DAC、ACC、AEC、cable、connector | Amphenol、TE Connectivity、Credo、Luxshare、Molex | 每 rack 连接数量、速率、良率、lead time、客户认证 |
| 液冷 / CDU | CDU、cold plate、manifold、quick disconnect、泵阀 | Vertiv、nVent、Schneider/Motivair、CoolIT、LiquidStack、Delta、Boyd | rack power density、CDU MW 订单、backlog、lead time、服务能力 |
| 数据中心电力 | 变压器、switchgear、UPS、PDU、储能、配电 | Vertiv、Eaton、Schneider、ABB、Siemens、GE Vernova、Hitachi Energy | transformer lead time、book-to-bill、grid interconnect、订单、capex |
| 电源管理 / power shelf | VRM、power shelf、HVDC、PSU | Delta、Lite-On、Monolithic Power、Vicor、Infineon、onsemi | 每 rack 功率、转换效率、attach rate、AI server 认证 |
| SSD / NAND | enterprise SSD、QLC、controller、NAND | Samsung、Micron、SK Hynix/Solidigm、Western Digital、Kioxia、Phison | AI storage attach、ASP、bit demand、库存、controller 供给 |
| HDD / 近线存储 | Nearline HDD、HAMR、数据湖 | Seagate、Western Digital、Toshiba | exabyte shipment、nearline ASP、cloud demand、库存 |
| 内存 / DDR / CXL | DDR5、MRDIMM、CXL memory | Micron、Samsung、SK Hynix、Rambus、Astera Labs | server DRAM content、CXL attach、ASP、平台支持 |
| 测试设备 | HBM 测试、SoC 测试、burn-in、probe card | Advantest、Teradyne、FormFactor、Cohu | tester bookings、AI/HBM test intensity、lead time、客户 capex |
| 半导体设备 | advanced packaging、etch/deposition、bonding、metrology | ASML、Applied Materials、Lam Research、KLA、ASM、BESI | AI capex、封装设备订单、交期、出口管制 |
| 半导体材料 | photoresist、substrate material、special gas、thermal materials | JSR、Shin-Etsu、Merck KGaA、Entegris、Resonac | 材料供应、价格、客户认证、产能 |
| AI server / rack integration | rack-scale server、ODM、system integration | Supermicro、Dell、HPE、Lenovo、Quanta、Wiwynn、Foxconn | rack shipments、GB200/GB300/Rubin 交付、毛利率、库存 |

## 动态新增候选来源

发现以下变化时，可新增不在固定池里的板块：
- 新 AI 系统架构改变 BOM 或部署瓶颈。
- 头部客户 capex、订单或产品路线图指向新瓶颈。
- 财报中多个代表公司同时出现异常增长或指引上修。
- 交期、价格、良率、库存或认证出现可验证异常。
- 新标准、reference design、OCP 项目或 NVIDIA/AMD/Broadcom 等生态变化创造新供应链位置。
