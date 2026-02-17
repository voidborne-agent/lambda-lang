# Lambda Lang 发布流程

每次更新 Lambda Lang 新版本时，按以下顺序执行：

## 1. 更新代码

- [ ] `src/atoms.json` — 更新 version 和 changelog
- [ ] `src/lambda_lang.py` — Python 翻译器
- [ ] `src/go/lambda.go` — Go 翻译器
- [ ] `src/roundtrip_test.py` — 添加/更新测试

## 2. 运行测试

```bash
cd src && python3 roundtrip_test.py
```

确保所有测试通过。

## 3. 更新文档

- [ ] `SKILL.md` — 更新版本号和变更说明
- [ ] `README.md` — 更新状态、Changelog、其他相关内容

## 4. 提交 Git

```bash
git add -A
git commit -m "release: vX.Y.Z - 变更描述"
git push origin main
```

## 5. 发布到 ClawHub

```bash
clawhub publish /path/to/lambda-lang --version X.Y.Z --changelog "变更说明"
```

## 6. 创建 GitHub Release

```bash
# 通过 API 或 GitHub UI 创建 release
# Tag: vX.Y.Z
# Title: vX.Y.Z - 简短描述
# Body: 详细变更说明
```

## 检查清单

| 步骤 | 完成 |
|------|------|
| atoms.json 版本更新 | ☐ |
| Python 翻译器更新 | ☐ |
| Go 翻译器更新 | ☐ |
| 测试通过 | ☐ |
| SKILL.md 更新 | ☐ |
| README.md 更新 | ☐ |
| Git 提交推送 | ☐ |
| ClawHub 发布 | ☐ |
| GitHub Release | ☐ |

---

*最后更新: v1.7.0 (2026-02-17)*
