# GitHub Actions Tag 发布流水线供应链安全审查器

针对开源模型网关 `codex2api` 遭黑客推送 Tag 绕开 PR 审核、导致 Release 带有无鉴权 RCE 后门并泄露 16 个 Secrets 的供应链灾难，构建的 CI/CD 风险审查与防护原型。

## 场景痛点
团队普遍对 `main` 主分支配置了严格的 Branch Protection，却往往忽视对 Git Tag 的保护；发布流水线监听 `on: push: tags` 导致恶意 Tag 直接触发带有高权 Secrets 的生产构建。

## 运行方式
```bash
python3 github_actions_tag_guard.py
```

## 核心机制
1. **Tag 保护规则审计 (Tag Protection Audit)**：检测仓库是否启用 Tag 保护与 GPG 签名核验，防止绕开 PR 触发构建；
2. **环境隔离门禁 (Environment Isolation)**：发布任务强制绑定 `environment` 并设置审批人，禁止在未受保护的任务中明文注入长期静态敏感凭据；
3. **不可变镜像摘要 (Immutable Digest)**：杜绝生产环境依赖 `:latest`，强制使用 sha256 镜像摘要与 Provenance 溯源。
