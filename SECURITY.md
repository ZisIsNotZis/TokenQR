# Security Policy

TokenQR 的设计目标是减少复制粘贴、聊天软件、截图和中间链路造成的 Token 泄露。电脑端临时生成密钥对，Provider 端使用公钥加密，Relay 不应能读取 Token。

TokenQR 不保护已经被攻破的电脑、恶意浏览器扩展、恶意 Provider 页面或已经获得解密后 Token 的应用。基础协议也不能替代 Provider 的真实撤销、过期、限额或审计能力。

请不要在公开 Issue 中提交任何 Token、私钥或完整 Relay endpoint。发现安全问题请先私下联系维护者，并提供复现步骤、影响范围和建议修复方式。
