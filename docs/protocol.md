# TokenQR Protocol Draft

## 目标

TokenQR 用一次性二维码建立电脑应用与 Token Provider 之间的授权信道。二维码只携带会话元数据和电脑端临时公钥；Provider Token 通过公钥加密后经任意 Relay 传输。

## QR payload

```json
{"v":"TQR1","r":"https://relay.example/relay/random","k":"base64url-public-key","a":"应用名称","p":"使用理由","e":1712345678}
```

- `v`：协议版本。
- `r`：一次性、不可预测的 Relay endpoint。
- `k`：电脑端临时公钥。
- `a`：应用名称。
- `p`：使用 Token 的理由。
- `e`：统一过期时间（Unix seconds）。

## Encrypted payload

```json
{"a":"应用名称","p":"使用理由","provider":"openai","base":"https://api.openai.com/v1","model":"gpt-4o-mini","allowed_models":["gpt-4o-mini"],"authorization":"Bearer ...","e":1712345678}
```

推荐浏览器原生 WebCrypto：P-256 ECDH、HKDF-SHA-256、AES-GCM。

## Relay contract

Relay 只需支持：向随机 endpoint 写入一条消息、读取一次消息、过期或删除消息。Relay 不需要理解 payload，也不应保存明文 Token。Relay 适配器可以是公共服务、本地 Python 服务或未来的其它实现。

## Policy semantics

`allowed_models`、限流、限量和有效期是授权意图；只有 Provider 或可选 Gateway 支持时才能强制执行。TokenQR 基础协议不要求部署 Gateway。
