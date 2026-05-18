# Wall-Breaker

「破壁机」深度内容自动化生产系统 MVP。

当前版本先打通 Phase 1 主链路：

```text
关键词/URL -> 多源素材采集 -> 原样入库 -> R1 辩证分析 -> V3 文案生成 -> 证据锚点与视觉时间轴 JSON
```

项目刻意把采集、分析、生成、视觉匹配拆成独立模块，后续可以逐步替换为真实百度/Bing、知乎、微博、B站、小红书 API 或 Playwright 爬虫。

## 快速开始

1. 复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

2. 在 `.env` 里填写 SiliconFlow Key：

```text
SILICONFLOW_API_KEY=sk-...
```

如果 `.env` 里有 `SILICONFLOW_BASE_URL`，建议使用官方 OpenAI-compatible 地址：

```text
SILICONFLOW_BASE_URL=https://api.siliconflow.com/v1
```

3. 运行一次 MVP：

```powershell
python -m wallbreaker.cli run "某个热点事件关键词"
```

默认会输出到 `runs/<时间戳>/`：

- `raw_items.jsonl`：原样素材库
- `analysis.json`：R1 结构分析
- `script.md`：V3 解说稿
- `visual_timeline.json`：证据锚点与视觉匹配时间轴
- `report.json`：本次任务总索引

如果没有配置 API Key，系统会使用本地 deterministic mock，方便先验证工程链路。

## 目录

```text
wallbreaker/
  cli.py                 # 命令行入口
  config.py              # 环境配置
  models.py              # 数据模型
  pipeline.py            # 编排主流程
  storage.py             # 原样 JSONL 入库
  llm/
    siliconflow.py       # SiliconFlow / DeepSeek 客户端
    prompts.py           # PRD Few-Shot 与系统提示词
  ingestion/
    sources.py           # 多源采集 adapter
  scripting/
    dialectical.py       # R1 分析 + V3 文案生成
  visual/
    matcher.py           # 文案后置视觉锚点生成
tests/
  test_pipeline.py
```

## 设计取舍

- **Anti-Summarization**：采集阶段只存 raw text、url、source、metadata，不提前摘要。
- **可替换采集器**：MVP 内置模拟源与通用搜索源接口，真实 API/Playwright 可以按 source adapter 接入。
- **证据优先**：文案生成后再做视觉匹配，避免“为了配图而写字”。
- **平台语境转化器**：文案 prompt 内置安全表达要求，保留逻辑锐度但降低具体指名风险。
