## Summary

<!-- 简述本次变更内容与动机 -->

## Change Type

- [ ] Bug fix
- [ ] Feature
- [ ] Refactor
- [ ] Documentation

## Architecture Check

- [ ] Page → VM → Facade → Service（分层正确）
- [ ] No sqlite3 outside storage（sqlite3 仅限 host/storage/）
- [ ] No PyQt5 in VM（VM 不依赖 UI 框架）
- [ ] No hardcoded colors（颜色走 Theme tokens）

## Testing

- Tests: <!-- 本地全量回归结果，如 988/988 PASS -->
- CI: <!-- GitHub Actions 运行状态 -->