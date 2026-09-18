# MiMo TTS × Reeden 集成

把小米 MiMo 的 **voicedesign 文字描述式音色**接入 Reeden 等阅读 App 的自建方案：**61 个中文人设音色** + **9 类情绪套路** + Cloudflare Worker 代理。

## 架构

```
Reeden (手机)
   │  POST /v1/audio/speech  {"model":"mimo-v2.5-tts-voicedesign","input":"<正文>","voice":"qingtian_shaonv"}
   │  Authorization: Bearer <WORKER_TOKEN>      ← 你的 Worker 鉴权（防白嫖）
   ▼
Cloudflare Worker  (本仓库 worker/)
   │  校验 token → 按 voice 查音色描述 → 转发 MiMo
   │  头: api-key: <MIMO_API_KEY>               ← 你的 MiMo key，只存在 Worker 环境变量
   ▼
MiMo API (voicedesign 模式，按描述"演"出人设)
   │  返回 base64 mp3
   ▼
Worker 解码 → audio/mpeg → Reeden 播放
```

- **MiMo key 永不落到手机端**：手机只持 Worker 的 Bearer token，被逆向也拿不到 MiMo key。
- **音色是人设描述，不是预置音频**：每次合成带描述现场演绎，所以单段约 5~8s（比预置音色慢，换来 61 种完整人设）。

## 目录

```
worker/mimo-tts-worker.js                     # Cloudflare Worker（容错解析 + X-Timing 调试头）
scripts/voices.json                           # 61 音色描述库（含 9 类情绪套路）
scripts/mimo-tts.py                           # 预置音色桥接（command provider）
scripts/mimo-voice.py                         # voicedesign / voiceclone 桥接
reeden/reeden-tts-mimo-config.example.json    # Reeden 导入配置模板（token 用占位符）
```

## 快速开始

### 1. 部署 Worker

```bash
cd worker
wrangler deploy
```

Worker 环境变量（`wrangler secret put`）：
| 变量 | 说明 |
|---|---|
| `API_KEY` | Worker 自身鉴权，即 Reeden 配置里的 `{{WORKER_TOKEN}}` |
| `MIMO_API_KEY` | MiMo key（`sk-` 按量 / `tp-` Token Plan） |
| `MIMO_BASE_URL` | 可选，默认 `https://api.xiaomimimo.com/v1` |

### 2. 导入 Reeden

1. 复制 `reeden/reeden-tts-mimo-config.example.json`
2. 把 `https://mimo-tts.YOUR-DOMAIN.com` 换成你的 Worker 域名
3. 把 `{{WORKER_TOKEN}}` 换成 Worker 的 `API_KEY`（**每一条都要换，或全文件替换**）
4. Reeden → 自定义 TTS → 从文件导入（**导入前先删旧分组**，Reeden 是合并不是覆盖）

### 3. 本地 Hermes 桥接（可选）

```bash
export MIMO_API_KEY=sk-xxx
python mimo-tts.py in.txt out.mp3 茉莉 mimo-v2.5-tts          # 预置音色
python mimo-voice.py mimo-v2.5-tts-voicedesign "音色描述" "文本" out.mp3   # 人设音色
```

## 音色与情绪套路

61 个音色（`scripts/voices.json`），其中 60 个按 9 类情绪套路优化描述：

| 类 | 数量 | 套路 |
|---|---|---|
| 悬疑 | 4 | 屏息感、压迫感 |
| 热血 | 6 | 冲劲、层层推进 |
| 甜宠 | 8 | 带笑、尾音俏皮 |
| 虐恋 | 6 | 隐忍破碎感 |
| 权谋 | 8 | 不怒自威、落锤重音 |
| 仙侠 | 4 | 缥缈余韵 |
| 市井 | 9 | 活色生香烟火气 |
| 温情 | 6 | 柔软安抚 |
| 克制 | 9 | 情绪藏在平稳下 |
| 妖女(魅惑) | 1 | 慵懒引诱 |
| 亲密旁白 | 1 | 情动高潮切入（情欲场景旁白专用） |

情绪套路五要素：**角色代入**（不是念稿而是在场景里说话）+ **开场状态前置**（直接从核心情绪切入）+ **拟声词演法** + **情绪梯度** + **负面清单**（绝无平铺直叙/播音腔）。

## 已知限制

- voicedesign 每次合成为独立采样（无固定 seed）：同一描述+文本，两次合成的语气/时长可能略有差异。
- 单段合成 5~8s（短段可能触发 Reeden 预合成跟不上，建议预合成并发 4→8）。
- Reeden 多角色 AI 识别依赖外部 LLM API（本仓库不含），识别 API 失效会降级导致人物错配。

## 安全

- 所有 key 用环境变量/占位符，仓库内不含任何真实密钥。
- Worker `API_KEY` 泄露时，改 Worker 环境变量后重新生成 Reeden 配置即可。
