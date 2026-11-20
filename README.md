# 出海护航 ExportGuard

跨境电商内容合规与多语言本地化 AI 工具链（AI+软件 · AI+数字内容IP出海）。

- 输入中文商品信息 → 生成合规、地道的目标市场英文内容
- 对商品文本做四类合规扫描（违禁词 / 认证缺失 / 敏感宣称 / 平台禁限售）
- 每条风险带法规/平台依据与修改建议，可溯源、可导出报告

## 目录结构

```
exportguard/
├── app.py                  # Streamlit 界面（Demo）
├── core/
│   ├── config.py           # 读取 .env 配置
│   ├── llm.py              # LLM 调用封装（OpenAI 兼容，支持 JSON 输出）
│   ├── generator.py        # 本地化生成
│   ├── compliance.py       # 规则库 + LLM 两层合规检测
│   └── report.py           # HTML 报告
├── rules/us_amazon.json    # 合规规则库（美国 + Amazon，可溯源）
├── data/
│   ├── products_sample.json# 8 个示例商品（含品类风险，供演示/评测）
│   └── eval_labels.json    # 金标准标注集
├── eval/metrics.py         # 评测脚本（准确率/召回率/F1）
├── requirements.txt
└── .env.example
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key（三选一，推荐 DeepSeek 最便宜）
#    复制 .env.example 为 .env，填入 LLM_API_KEY
#    DeepSeek:  BASE_URL=https://api.deepseek.com   MODEL=deepseek-chat
#    通义千问:  BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1  MODEL=qwen-plus
#    智谱GLM:   BASE_URL=https://open.bigmodel.cn/api/paas/v4  MODEL=glm-4-flash

# 3. 启动 Demo
streamlit run app.py
```

## 评测（得到"可验证"的硬指标）

```bash
# 全系统（生成 + 规则库 + LLM）：需先配置 API Key
python eval/metrics.py

# 仅规则库（离线、确定性基线，无需 API Key）
python eval/metrics.py --rules-only

# 保存检测结果
python eval/metrics.py --rules-only --save
```

**预期确定性基线（仅规则库）**：精确率 1.000、召回率 0.833、F1 0.909（规则库能命中 12 条金标中的 10 条；ASTM F963、FDA MoCRA 注册这两条隐性风险需 LLM 层补足）。跑全系统后，召回率会进一步上升——把真实数字填进 `04-方案说明-初稿.md`。

## 说明

1. **规则库可溯源**：每条规则带 `basis_url` 官方链接，报告里可点开核查，这是"可验证"的关键证据。
2. **检测同时扫描中文原始宣称与英文生成内容**：避免生成时"洗掉"风险表述导致漏检。
3. 示例商品为演示用；正式提交前，按 `02-数据采集清单.md` 换成 30~50 个真实 1688/Amazon 商品。

## 提交前检查

- [ ] `04-方案说明-初稿.md` 的【占位】已替换为真实数字与 Demo/仓库链接
- [ ] 按 `05-演示视频脚本.md` 录好 2 分钟视频
- [ ] 代码已推 GitHub（README、运行说明、规则库、标注集齐全）
- [ ] Demo 已部署可访问（或提供本地运行方式）
