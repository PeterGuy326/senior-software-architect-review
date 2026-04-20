# 17 · 案例：安全架构（教材第 18 章）

## 核心概念

- **纵深防御**：边界 / 网络 / 主机 / 应用 / 数据多层防御
- **零信任**（Zero Trust）：Never trust, always verify
- **STRIDE 威胁建模**：Spoofing / Tampering / Repudiation / Information Disclosure / DoS / Elevation of Privilege
- **DREAD 风险评估**：Damage / Reproducibility / Exploitability / Affected users / Discoverability

## 典型防护

| 层次 | 威胁 | 对策 |
|---|---|---|
| 网络 | DDoS | 清洗、CDN、WAF |
| 主机 | 入侵 | HIDS、漏洞扫描、加固 |
| 应用 | SQL 注入/XSS/CSRF | 参数化查询、CSP、Token |
| 数据 | 泄露 | 加密、脱敏、DLP |
| 身份 | 凭据窃取 | MFA、SSO、最小权限 |

## 案例题常见问法

- 画出安全架构图
- STRIDE 识别威胁 + 对策
- 数据分级分类 + 加密方案

## TODO

- [ ] 等保 2.0 技术要求速查
