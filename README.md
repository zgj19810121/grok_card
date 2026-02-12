# grok_card
一个用于grok自动绑卡以获得supper试用资格的脚本.
# 网页自动化模拟服务 - 使用说明

## 项目结构

```
模拟/
├── install.bat               # 一键安装依赖
├── run.bat                   # 启动 HTTP API 服务
├── server.py                 # HTTP API 服务
├── engine.py                 # 自动化执行引擎
├── open_browser.py           # 快速打开 camoufox 浏览器（调试用）
├── requirements.txt          # Python 依赖
└── tasks/                    # 任务配置目录
    ├── template.yaml         # 完整模板（所有操作参考）
    └── stripe_checkout.yaml  # Grok 注册 + Stripe 支付实例
```

---

## 一、安装

双击 `install.bat`，或手动执行：

```bash
pip install -r requirements.txt
python -m patchright install chromium
python -m camoufox fetch
```

依赖说明：
- **patchright** — 反检测 Playwright 分支
- **camoufox** — 反检测 Firefox 浏览器
- **pyyaml** — YAML 配置解析
- **flask** — HTTP API 服务

---

## 二、运行方式

### 方式1：HTTP API 服务

双击 `run.bat`（自动杀旧进程再启动），或：

```bash
python server.py
# 服务运行在 http://localhost:5000
```

API 接口：

**启动任务（异步，立即返回 task_id）**
```
POST http://localhost:5000/run
Content-Type: application/json

{"task": "tasks/stripe_checkout.yaml"}

// 传变量覆盖 YAML 默认值
{"task": "tasks/stripe_checkout.yaml", "vars": {"邮箱": "xxx", "密码": "xxx"}}
```

**查询任务状态**
```
GET http://localhost:5000/status/1
```

**列出所有任务**
```
GET http://localhost:5000/tasks
```

**清理已完成的任务**
```
POST http://localhost:5000/clear
```

### 方式2：Python 直接调用

```python
from engine import run_task

success, logs = run_task("tasks/stripe_checkout.yaml")

# 传变量覆盖
success, logs = run_task("tasks/stripe_checkout.yaml", {
    "邮箱": "test@example.com",
    "密码": "mypass"
})
```

---

## 三、YAML 配置文件

在 `tasks/` 目录下创建 `.yaml` 文件。可复制 `template.yaml` 修改。

### 基本结构

```yaml
name: 任务名称
url: https://example.com

browser:
  headless: false               # false=显示浏览器  true=后台运行
  engine: camoufox              # camoufox（反检测）或 patchright（默认）
  channel: "msedge"             # 浏览器通道：msedge, chrome, 或留空
  incognito: true               # 无痕模式
  # user_data_dir: "./data"     # 持久化目录，保留登录状态
  # slow_mo: 500                # 全局慢动作（毫秒）

timing:
  step_delay: [1000, 3000]      # 每步随机延迟（毫秒）
  human_mouse: true             # 贝塞尔曲线鼠标轨迹

vars:
  用户名: "test_user"
  密码: "test_pass"

steps:
  - action: type
    selector: "#username"
    value: "{{用户名}}"
```

### 浏览器引擎

| 引擎 | 说明 |
|------|------|
| `patchright` | 默认，基于 Chromium，支持 channel 切换 |
| `camoufox` | 反检测 Firefox，适合有 bot 检测的网站 |

---

## 四、所有支持的操作

### 点击

```yaml
- action: click
  selector: 'button:has-text("Submit")'
  timeout: 15000          # 可选，默认 30000
  force: true             # 可选，跳过可见性检查
  frame: 'iframe[src*="x.com"]'  # 可选，iframe 内操作

# 坐标点击（用于 closed shadow-root 等无法选择的元素）
- action: click_pos
  js: >
    (() => {
      const el = document.querySelector('#ref');
      const rect = el.getBoundingClientRect();
      return {x: rect.x + 20, y: rect.y + 10};
    })()
```

### 输入

```yaml
# 逐字输入（模拟真人打字）
- action: type
  selector: '[name="email"]'
  value: "{{用户名}}"
  type_delay: [100, 300]        # 每字符随机延迟

# 直接填充（瞬间填入）
- action: fill
  selector: '#search'
  value: "search text"

# 按键
- action: press
  selector: '#input'
  key: "Enter"                  # 支持 Tab, Escape, Control+a 等
```

### 表单

```yaml
- action: check                 # 勾选
  selector: '#agree'

- action: uncheck               # 取消勾选
  selector: '#newsletter'

- action: select                # 下拉选择
  selector: '#country'
  value: "CN"

- action: upload                # 上传文件
  selector: '#file-input'
  files: "path/to/file.png"
```

### 等待

```yaml
# 等待元素出现
- action: wait
  selector: '#login-form'
  timeout: 60000

# 等待 URL 包含关键字
- action: wait_url
  pattern: "dashboard"          # 自动包装为 **dashboard**
  timeout: 60000

# 固定/随机等待
- action: sleep
  duration: 3000                # 或 [2000, 5000] 随机
```

### 导航

```yaml
- action: goto
  url: "https://example.com/page2"

- action: back
- action: forward
- action: reload
```

### 鼠标

```yaml
- action: hover
  selector: '#menu'

- action: mouse_move
  x: 500
  y: 300
```

### 其他

```yaml
- action: focus
  selector: '#input'

- action: scroll
  selector: '#footer'           # 滚动到元素
  # 或 y: 500                   # 滚动指定像素

- action: screenshot
  path: "result.png"

- action: js
  script: "document.title"      # 返回值记录到日志
```

### 流程控制

```yaml
# 循环
- action: loop
  count: 3
  steps:
    - action: click
      selector: '#next'

# 条件执行（元素存在才执行）
- action: if_exists
  selector: '#popup'
  steps:
    - action: click
      selector: '#close-popup'

# 条件重试（轮询直到条件满足）
- action: retry_until
  selector: '#success'              # CSS 选择器条件
  # js_condition: "expr"            # 或 JS 表达式条件
  max_retries: 5
  retry_delay: [3000, 5000]
  steps:                            # 每次重试执行的操作
    - action: click
      selector: '#retry-btn'
  on_success:                       # 条件满足后执行
    - action: click
      selector: '#continue'
```

---

## 五、延迟控制

任何步骤都可以加延迟参数：

```yaml
- action: click
  selector: "#btn"
  delay_before: [500, 1500]     # 执行前等待，覆盖全局 step_delay
  delay_after: 1000             # 执行后等待
```

所有时间参数支持：固定值 `500` 或随机范围 `[500, 1500]`。

---

## 六、变量系统

YAML 中 `vars` 定义默认值，steps 中用 `{{变量名}}` 引用。调用时传入的变量会覆盖默认值。

变量名支持中文、英文、数字，只要 key 和 `{{}}` 里的名字一致即可。

---

## 七、selector 写法速查

| 写法 | 含义 | 示例 |
|------|------|------|
| `#id` | 按 id | `#username` |
| `.class` | 按 class | `.btn-primary` |
| `[attr="val"]` | 按属性 | `[data-testid="login"]` |
| `tag` | 按标签 | `button` |
| `:has-text("文本")` | 按文本内容 | `button:has-text("登录")` |
| `#a .b` | 后代选择 | `#form .submit` |
| `#a > .b` | 直接子元素 | `#nav > .item` |

---

## 八、获取 selector 的方法

### 方法1：Playwright Codegen（推荐）

```bash
python -m patchright codegen https://example.com
```

打开两个窗口：左边浏览器操作，右边自动生成代码和 selector。

### 方法2：浏览器 F12

1. 打开目标网页，按 F12
2. 点左上角箭头图标（选择元素工具）
3. 点击页面元素
4. Elements 面板中右键 → Copy → Copy selector

---

## 九、常见问题

**元素找不到？**
- F12 确认 selector 是否正确
- 用 `wait` 等元素出现，不要用 `sleep`
- 元素可能在 iframe 里，加 `frame` 字段
- Cloudflare 等组件在 closed shadow-root 内，用 `click_pos` 坐标点击

**点击被遮挡？** 加 `force: true`

**怎么调试？**
- `headless: false` 看浏览器操作
- `slow_mo: 1000` 放慢速度
- 出错自动截图 `error.png`
- 日志显示卡在第几步

**验证码？**
- CF Turnstile：用 `retry_until` + `click_pos` 动态坐标点击（参考 stripe_checkout.yaml）
- 其他验证码：用 `sleep` 暂停手动处理，或用 `user_data_dir` 持久化登录减少验证码
