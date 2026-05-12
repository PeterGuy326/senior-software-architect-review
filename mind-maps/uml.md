# UML 脑图（14 种图 + 关系）

```mermaid
mindmap
  root((UML 2.x))
    结构图 7
      类图 Class
        类 属性 操作
        关系 6种
      对象图 Object
      包图 Package
      组件图 Component
      部署图 Deployment
      组合结构图 Composite
      制品图 Artifact
    行为图 7
      用例图 Use Case
        参与者 用例 系统边界
      活动图 Activity
        泳道 决策 并发
      状态图 State
        状态 转换 触发
      序列图 Sequence
        生命线 消息 激活
      通信图 Communication
        Collaboration
      时序图 Timing
      交互概览图
    交互图 4子类
      序列 通信 时序 交互概览
```

## 类关系六种（必记）

```mermaid
graph LR
    A[类关系] --> B[泛化 Generalization<br/>is-a 继承<br/>实线空心三角]
    A --> C[实现 Realization<br/>实现接口<br/>虚线空心三角]
    A --> D[依赖 Dependency<br/>use 临时使用<br/>虚线箭头]
    A --> E[关联 Association<br/>has-a 长期持有<br/>实线箭头]
    A --> F[聚合 Aggregation<br/>整体-部分 弱<br/>实线空心菱形]
    A --> G[组合 Composition<br/>整体-部分 强<br/>实线实心菱形]
```

## 类关系强弱排序

```
依赖 < 关联 < 聚合 < 组合 < 泛化 / 实现
（耦合从弱到强）
```

## 何时选哪种图

```mermaid
graph TD
    Q{要表达什么?}
    Q -->|系统功能 用户视角| UC[用例图]
    Q -->|静态结构 类与关系| CD[类图]
    Q -->|对象间消息时序| SD[序列图]
    Q -->|对象状态变化| ST[状态图]
    Q -->|业务流程 并发| AD[活动图]
    Q -->|部署节点 物理拓扑| DP[部署图]
    Q -->|模块依赖 编译单元| CP[组件图]
```

## 用例图三要素

```mermaid
graph LR
    A[参与者<br/>Actor] -->|交互| B[用例<br/>Use Case]
    B -->|位于| C[系统边界]
    B -.->|<<include>>| D[基本用例]
    B -.->|<<extend>>| E[扩展用例]
```

## 序列图 vs 活动图选择

| 想表达 | 选 |
|---|---|
| **对象间消息时序**（谁调用谁、什么顺序） | 序列图 |
| **流程/工作流**（决策、并发、分支） | 活动图 |
| **单个对象的生命周期** | 状态图 |
| **同一时刻多对象交互结构** | 通信图 |

## 速记口诀

- **结构 7 类**：类 / 对象 / 包 / 组件 / 部署 / 组合 / 制品
- **行为 7 图**：用例 / 活动 / 状态 / 序列 / 通信 / 时序 / 交互概览
- **6 种关系**：依赖 / 关联 / 聚合 / 组合 / 泛化 / 实现
- 聚合 vs 组合：**聚合可分离（部门-员工）、组合同生死（人-心脏）**
