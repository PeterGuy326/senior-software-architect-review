# 信息安全脑图

```mermaid
mindmap
  root((信息安全))
    CIA 三要素
      机密性 Confidentiality
        加密
        访问控制
      完整性 Integrity
        哈希 / HMAC
        数字签名
      可用性 Availability
        冗余 / 备份
        抗 DDoS
    威胁建模 STRIDE
      Spoofing 伪装
        对策 认证
      Tampering 篡改
        对策 哈希签名
      Repudiation 否认
        对策 审计日志 不可否认
      Information disclosure 信息泄露
        对策 加密 访问控制
      Denial of Service 拒绝服务
        对策 限流 高可用 抗 DDoS
      Elevation of privilege 提权
        对策 最小权限 沙箱
    密码学
      对称加密
        DES / 3DES / AES
        国密 SM1 SM4 SM7
        快 适合大数据
      非对称加密
        RSA / ECC / DSA
        国密 SM2 SM9
        慢 解决密钥分发
      哈希
        MD5 已破解
        SHA-1 / SHA-256
        国密 SM3
      数字签名
        私钥签 公钥验
        防抵赖 + 完整性
      PKI / CA
        数字证书 X.509
        证书链
    身份认证
      Authentication 你是谁
        密码 + 多因素 MFA
        生物识别
        证书认证
      Authorization 你能做什么
        RBAC 角色
        ABAC 属性
        ACL 访问控制列表
      SSO 单点登录
        SAML
        OAuth 2.0
        OIDC
        JWT Token
    网络安全
      防火墙
        包过滤
        状态检测
        应用代理
        WAF Web 防火墙
      IDS / IPS
        入侵检测 / 防御
      VPN
        IPSec
        SSL VPN
      DMZ 隔离区
      零信任 ZTNA
    应用安全
      OWASP Top 10
        注入 SQL/Command
        失效身份认证
        敏感数据暴露
        XXE
        失效访问控制
        安全配置错误
        XSS
        不安全反序列化
        组件漏洞
        日志监控不足
      安全开发 SDL
        S-SDLC
      代码审计
      渗透测试
    国家标准
      等级保护 2.0
        一级 自主保护
        二级 指导保护
        三级 监督保护 核心
        四级 强制保护
        五级 专控保护
      国密算法
        SM1 SM4 SM7 对称
        SM2 SM9 非对称
        SM3 哈希
      网络安全法 / 数据安全法 / 个人信息保护法
```

## CIA 与对策矩阵

```mermaid
graph LR
    C[机密性] -->|对策| C1[加密 AES/SM4]
    C -->|对策| C2[访问控制 RBAC]
    I[完整性] -->|对策| I1[哈希 SHA-256/SM3]
    I -->|对策| I2[数字签名]
    A[可用性] -->|对策| A1[冗余高可用]
    A -->|对策| A2[限流抗DDoS]
```

## STRIDE 速查

| 威胁 | 含义 | 对策 |
|---|---|---|
| **S**poofing | 伪装身份 | 强认证 + MFA |
| **T**ampering | 数据篡改 | 哈希 + 签名 |
| **R**epudiation | 否认操作 | 审计日志 + 不可否认签名 |
| **I**nfo disclosure | 信息泄露 | 加密 + 访问控制 |
| **D**oS | 拒绝服务 | 限流 + 高可用 + WAF |
| **E**lev of privilege | 提权 | 最小权限 + 沙箱 |

## 加密算法选型

```mermaid
graph TD
    Q{需求} -->|大量数据加密| Sym[对称: AES-256 / SM4]
    Q -->|密钥协商/数字签名| Asym[非对称: RSA-2048 / ECC / SM2]
    Q -->|数据指纹/完整性| Hash[哈希: SHA-256 / SM3]
    Q -->|防抵赖| Sig[签名: 私钥签+公钥验]
    Q -->|国密合规| GM[国密 SM 系列]
```

## 等保 2.0 五级

```
一级 自主 → 二级 指导 → 三级 监督（互联网企业核心系统主流） → 四级 强制 → 五级 专控
```

## 速记口诀

- **CIA**：机密 / 完整 / 可用——一切安全设计的初心
- **STRIDE**：伪 / 篡 / 抵 / 泄 / 拒 / 提——威胁建模的标准锤
- **国密**：**SM2 非对称 / SM3 哈希 / SM4 对称**——这三个最常考
- **AuthN ≠ AuthZ**：认证（你是谁）≠ 授权（你能做什么）
