# Contributing

TokenQR 的核心目标是推广一个开放的、可互操作的 Token 授权协议，而不是绑定某个客户端或云服务。

## 提交建议

- 优先改进协议清晰度、互操作性和安全边界。
- 不要把 Provider Token、私钥或真实 Relay 凭据提交到仓库。
- 新增 Provider 时保留 OpenAI-compatible fallback。
- 让浏览器端保持无第三方运行时依赖。
- 提交前运行 `node --check` 对内嵌脚本进行语法检查，并运行 `git diff --check`。

## Issue 方向

欢迎讨论协议设计、Relay 适配器、浏览器兼容性、Provider 适配和安全模型。TokenQR 不承诺客户端能够强制执行没有 Provider 或 Gateway 支持的限流、限量和撤销策略。
