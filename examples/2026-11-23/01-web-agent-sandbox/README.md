# Web Agent 间接提示词注入防御沙箱原型

针对 Web 智能体（Playwright、Puppeteer、基于 LLM 的自主浏览代理）在访问不可信外部网页时面临的间接提示词注入（Indirect Prompt Injection）风险，借鉴谷歌 Chrome AI 安全团队 Mirror Dimension（镜像宇宙）理念构建的防御演示。

## 场景痛点
网页中埋设了不可见文字（如 `style="display:none; font-size:0px;"`）或伪造的管理指令。未防护的智能体在读取全量 DOM 文本后被恶意注入劫持，执行越权转账等破坏操作。

## 运行方式
```bash
python3 web_agent_injection_sandbox.py
```

## 核心机制
1. **DOM 结构提纯 (DOM Sanitizer)**：剥离不可见 CSS 容器、隐藏标签及内联脚本；
2. **行为边界断言网关 (Action Guardrail)**：在动作出网前强制对齐用户原始目标白名单，阻断越权越级操作。
