# 知识点 21 · 安全架构

## 一、核心概念

### CIA 三要素

- **C**onfidentiality 保密性
- **I**ntegrity 完整性
- **A**vailability 可用性

### STRIDE 威胁建模

| 威胁 | 对策 |
|---|---|
| **S**poofing 身份伪造 | 认证（MFA） |
| **T**ampering 篡改 | HMAC / 数字签名 |
| **R**epudiation 抵赖 | 数字签名 + 日志 |
| **I**nfo Disclosure 泄露 | 加密（TLS / AES） |
| **D**oS 拒绝服务 | 限流 / WAF / DDoS 清洗 |
| **E**levation of Privilege 提权 | 最小权限 / RBAC |

### 密码学

| 类型 | 代表 | 国密 |
|---|---|---|
| 对称 | **AES** / 3DES | **SM4** |
| 非对称 | **RSA** / ECC | **SM2** |
| Hash | **SHA-256** / MD5 | **SM3** |

**数字签名**：**私钥签 + 公钥验**（保证不可抵赖 + 完整性）

### 纵深防御 5 层

1. 网络（防火墙 / WAF / DDoS）
2. 主机（HIDS / 基线 / 漏扫）
3. 应用（**SSO + MFA + RBAC** + 输入校验）
4. 数据（TLS + AES + 脱敏 + KMS）
5. 审计（日志 + SIEM）

### 等保 2.0

- 5 级（一般系统**三级**起）
- 10 项要求（5 技术 + 5 管理）

## 二、关联资源

- 速查：[cheatsheets/iso25010.md](../cheatsheets/iso25010.md)
- 论文主题：[past-papers/paper-topics/04-security-design.md](../past-papers/paper-topics/04-security-design.md)
- 案例题型：[past-papers/case-types/07-security-architecture.md](../past-papers/case-types/07-security-architecture.md)

## 三、典型例题

### 📚 选择题 1（威胁分类）

"SQL 注入"属于 STRIDE 中的：
- A. Spoofing  B. **Tampering**  C. Repudiation  D. DoS

**答案**：B（篡改后端数据 / 查询）

### 📚 选择题 2（数字签名）

数字签名**不能**提供的安全属性：
- A. 不可抵赖  B. 完整性  C. 身份认证  D. **保密性**

**答案**：D（签名仅用私钥签，不加密原文）

### 📚 选择题 3（国密算法）

下列属于国密**非对称**加密的是：
- A. SM3  B. **SM2**  C. SM4  D. AES

**答案**：B

### 🎯 案例填空：密码存储方案

❌ **MD5(password)** → 可被彩虹表破解
✅ **Bcrypt / Scrypt / Argon2**（加盐 + 慢哈希）+ 每用户独立盐

### ✍️ 论文场景

"依据 **STRIDE** 识别威胁，通过**纵深防御**五层（网络 / 主机 / 应用 / 数据 / 审计）构建；核心数据 **AES-256-GCM** + **KMS 密钥 90 天轮换**；身份认证采用 **SSO + MFA**，授权 **RBAC** 细化到字段级；满足**等保三级**合规。"
