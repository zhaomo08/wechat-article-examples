# 示例：PowerShell 5.1 -> 7 迁移踩坑排查

验证 CI/CD 与部署流水线中从 Windows PowerShell 5.1 迁移到 PowerShell 7 的三大隐蔽坑：

1. **UTF-16LE BOM 编码陷阱**：下游解析器抛出 `invalid start byte`。
2. **ConvertFrom-Json 深度截断**：默认 Depth=2 导致深层配置退化为字符串，访问属性崩溃。
3. **原生外部命令退出码被吞**：5.1 默认 `$ErrorActionPreference='Stop'` 无法拦截构建失败。

## 运行方式

```bash
python3 pwsh_migration_check.py
```
