# Optional Gateway

TokenQR 基础模式把 Provider Token 端到端交给本地应用；Gateway 模式是可选扩展，用于 Provider 不支持子 Token、限流、限量或撤销时提供这些能力。

## LiteLLM 方向

LiteLLM Proxy 可以作为 TokenQR 的可选 Gateway：

```text
Provider Token -> LiteLLM Proxy -> 应用专用 Virtual Key -> AI 应用
```

Gateway 应保存上游 Provider Key；TokenQR 手机端只授权 Gateway 创建或启用一枚应用专用 Key。应用不需要接触上游主 Token。

## 当前状态

本目录先记录集成边界，不会在基础 POC 中强制引入 LiteLLM。下一步需要固定：

1. LiteLLM 部署方式和版本；
2. Virtual Key 创建接口；
3. 模型白名单、RPM/TPM 和预算字段映射；
4. Key 过期和撤销接口；
5. Gateway 返回给电脑端的 endpoint、model 和 key 格式；
6. 本地开发用 Docker Compose 配置。

任何 Gateway 凭据都必须通过环境变量或 Secret 管理，不能提交到仓库。
