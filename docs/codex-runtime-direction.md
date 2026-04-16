# Codex Runtime 技术方向

## 背景与约束

本项目后续技术方向以 Codex 产品能力为核心，而不是以 OpenAI API Key 为核心。

当前关键约束：

- 不接受 `OPENAI_API_KEY` 带来的 API billing 成本作为默认使用路径。
- 默认只接受 ChatGPT Pro / Codex 账号订阅额度。
- 不引入 OpenAI Agents SDK 路线，因为它默认面向 OpenAI API 调用和 API 计费。
- 不重造一个低配 coding agent；优先复用 Codex 已经具备的 agent harness、工具、权限、会话和执行能力。

因此，本项目应定位为 subscription-backed Codex autonomous coding quickstart，而不是 API-key-backed Agents SDK quickstart。

## 技术方向

项目外层只负责 workflow orchestration，底层 coding agent 执行交给 Codex。

外层 orchestration 负责：

- 任务分解和轮次控制
- feature list 和进度记录
- 验收标准和验证状态
- resume / continue 策略
- 产物和项目状态管理
- Codex runtime 的选择和兼容

底层 Codex 负责：

- 代码库理解
- 文件读写
- shell 命令执行
- patch 生成和应用
- 测试、调试和修复循环
- 会话上下文和 agent 工具使用
- 权限、审批和 sandbox 行为

这意味着本项目的价值不在于重新实现 agent 工具链，而在于把 Codex 产品能力组织成可重复、可恢复、可验证的 quickstart workflow。

## Runtime 选择

Runtime 优先级如下。

1. `@openai/codex-sdk`

   当前一等 runtime。用于以可编程方式控制 Codex agent，适合实现 thread / run / resume 形式的 agent loop。自主编码 harness 默认应优先走 Codex SDK runtime。

2. `codex exec`

   兼容 fallback。适合快速跑通、脚本化执行、环境验证和低依赖场景。它可以继续保留为默认可用路径或 fallback 路径，但长期不应替代 Codex SDK 的可编程 runtime 角色。

3. `codex app-server`

   高级集成路线。适合自定义 UI、事件流、审批流、会话历史和产品化控制台。如果项目后续从 quickstart 走向完整产品界面，可以基于 app-server 做深度集成。

明确不支持：

- `openai-agents` / OpenAI Agents SDK。当前项目不支持 API-key-backed runtime，不暴露 `agents-sdk` 选项，也不保留相关依赖。

## 对当前 Quickstart 的影响

当前 `autonomous-coding` quickstart 应从“同时展示 Codex CLI 和 Agents SDK 两种 runtime”调整为“Codex SDK 一等、Codex CLI 兜底、无 Agents SDK 路线”的 autonomous coding quickstart。

具体影响：

- 新增并默认优先选择 `codex-sdk` runtime。
- 保留现有 `codex-cli` runtime，作为可直接运行的兼容路径。
- 移除 `agents-sdk` runtime，不再暴露 API-key-backed optional mode。
- README 和使用说明应避免暗示用户必须配置 `OPENAI_API_KEY` 才能体验主流程。
- 项目叙事应强调“复用 Codex 产品能力”，而不是“自建 OpenAI Agents SDK sandbox agent”。

## 当前实现要求

当前实现应满足：

1. 明确当前 quickstart 的默认 runtime 策略：优先 Codex SDK，CLI 仅作为 fallback。
2. 使用 `@openai/codex-sdk` runtime 管理 thread / run / resume。
3. 保留 `codex exec` runtime 作为 fallback，并继续支持脚本化运行。
4. 移除 `agents-sdk` runtime 文档和代码，避免和主路线混淆。
5. 如果需要更强产品化能力，再评估 `codex app-server`，用于事件流、审批和自定义 UI。

验收标准：

- 文档明确写出不以 API Key / Agents SDK 为默认路线。
- 文档明确写出 Codex SDK 优先于 `codex exec` 的长期方向。
- 文档明确写出外层只做 workflow orchestration，底层 coding agent 执行交给 Codex。
- 不修改 AGENTS 指令，不把项目技术决策混入全局 agent 工作规范。
