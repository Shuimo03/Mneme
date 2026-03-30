# **Python 3 + FastAPI 代码规范（Draft v1）**

## **1. 目标**

本规范用于约束 Mneme 及后续 Python 3 + FastAPI 项目的代码风格、目录结构、类型系统、接口设计、配置管理、日志、测试和 CI 规则。

目标不是追求“最花哨”的写法，而是保证代码具备以下特点：

- 可读
- 可维护
- 可测试
- 可替换
- 可被未来的人类和智能体稳定理解

FastAPI 本身基于标准 Python 类型提示工作，因此本规范默认采用“类型优先”的工程风格。

---

## **2. 总体原则**

### **2.1 类型优先**

所有公共函数、方法、服务接口、依赖函数都必须写完整类型标注。  
请求体和响应体必须使用 Pydantic 模型，不允许在 API 边界长期传递无约束的裸 `dict`。

### **2.2 边界清晰**

路由层只处理 HTTP 相关逻辑：

- 参数解析
- 鉴权
- 状态码
- 响应模型

业务逻辑放在 `services/`，外部系统交互放在 `clients/` 或 `repositories/`。

### **2.3 验证前置**

所有外部输入都必须在边界层完成验证，包括：

- HTTP 请求
- 环境变量
- 定时任务输入
- LLM 输出
- 第三方 API 返回结果

### **2.4 配置集中**

不得在业务代码中到处直接调用 `os.getenv()`。  
配置必须统一进入 `Settings` 对象，并通过依赖注入或生命周期管理传入。

### **2.5 生命周期集中**

数据库连接池、HTTP 客户端、模型实例、缓存连接等应用级资源，统一通过 `lifespan` 管理，不得散落在全局变量初始化或隐式副作用中。

### **2.6 可测试优先**

所有外部依赖都应可替换。  
测试中优先使用 FastAPI 的依赖覆盖机制，不依赖大量 monkeypatch。

---

## **3. 目录结构规范**

推荐目录结构如下：

```
app/
  main.py
  api/
    router.py
    routes/
      articles.py
      digests.py
      health.py
  core/
    config.py
    lifespan.py
    logging.py
    exceptions.py
  schemas/
    article.py
    digest.py
    common.py
  services/
    article_service.py
    summary_service.py
    digest_service.py
  repositories/
    article_repository.py
  clients/
    openai_client.py
    claude_client.py
    im_client.py
  domain/
    models.py
    enums.py
tests/
  api/
  services/
  repositories/
  integration/
scripts/
docs/
```

### **目录职责**

- `api/`：HTTP 路由层
- `schemas/`：请求/响应模型
- `services/`：业务逻辑
- `repositories/`：数据库读写
- `clients/`：第三方依赖封装
- `core/`：基础设施与应用装配
- `domain/`：领域枚举、领域对象、纯业务概念

### **禁止事项**

- 禁止出现 `utils.py`、`common.py`、`misc.py` 这种职责模糊的“垃圾桶文件”
- 禁止把数据库模型、API 模型、领域模型揉成一个类
- 禁止在 `main.py` 中堆积业务逻辑

---

## **4. Python 基础风格规范**

### **4.1 命名**

遵循 PEP 8：

- 模块名、包名、函数名、变量名：`snake_case`
- 类名：`CapWords`
- 常量：`UPPER_CASE`
- 私有属性/方法：前缀 `_`
- 布尔变量优先使用可读命名，如 `is_active`、`has_error`

### **4.2 导入**

- 标准库、第三方、本地模块分组导入
- 禁止 `from x import *`
- 禁止未使用导入
- 统一由格式化工具处理导入顺序

### **4.3 Docstring**

遵循 PEP 257：

- 公共模块、公共类、公共函数、公共方法必须有 docstring
- 私有函数如果逻辑不直观，也应补简要说明
- Docstring 重点说明行为、参数、返回值、副作用、异常和使用限制

---

## **5. 类型与 Pydantic 规范**

### **5.1 类型标注**

- 所有公共函数必须标注参数与返回值类型
- 不允许在公共接口中省略返回类型
- 尽量避免使用 `Any`
- 优先使用明确的联合、枚举、泛型、字面量类型

### **5.2 Pydantic 模型使用原则**

- API 请求体必须使用输入模型
- API 响应必须使用输出模型
- 第三方返回数据先映射到内部模型，再进入业务逻辑
- LLM 输出必须先过 Pydantic 校验，再入库或展示

### **5.3 校验器**

- 简单字段约束优先用字段类型和约束表达
- 字段级复杂逻辑使用 field validator
- 跨字段不变量使用 model validator
- 不允许把大量校验逻辑塞进路由函数

---

## **6. FastAPI 路由与依赖规范**

### **6.1 路由层必须轻薄**

每个 endpoint 只做这些事：

- 读取和声明输入
- 调用 service
- 映射输出
- 设置状态码
- 抛出 HTTP 层异常

不得在 endpoint 中直接写：

- SQL
- 大段业务分支
- 第三方 SDK 调用细节
- 复杂对象拼装

### **6.2 `response_model` 必须显式声明**

除极少数特殊场景外，所有返回 JSON 的 endpoint 都应声明 `response_model`。

### **6.3 依赖注入**

- 配置对象通过依赖注入提供
- 数据库 session 通过依赖注入提供
- 当前用户/权限校验通过依赖注入提供
- 外部 client 可通过依赖注入或应用状态统一提供

### **6.4 `async def` 使用规则**

- 调用可 `await` 的库时，用 `async def`
- 调用阻塞型库时，优先使用普通 `def`
- 不为了“统一风格”而强行异步化同步代码

---

## **7. 配置与生命周期规范**

### **7.1 Settings**

统一使用 `Settings` 类管理配置，例如：

- 应用名
- 环境
- 数据库 DSN
- LLM API Key
- IM 推送配置
- 开关类配置

### **7.2 Lifespan**

以下资源必须在 `lifespan` 中初始化和释放：

- 数据库连接池
- HTTP 客户端
- Redis 客户端
- 模型实例
- 消息队列生产者

---

## **8. 日志与异常规范**

### **8.1 日志**

统一使用标准库 `logging`，禁止 `print()` 作为正式日志方案。

### **8.2 日志要求**

- 统一在 `core/logging.py` 中配置
- 输出必须包含时间、级别、logger 名称
- 接口请求日志应附带 request id / trace id
- 异常必须使用结构化方式记录上下文
- 不记录明文密钥、token、敏感个人信息

### **8.3 异常处理**

- 业务异常与 HTTP 异常分离
- service 层抛业务异常
- 路由层或统一异常处理器映射为 HTTP 响应
- 不允许大量 `except Exception: pass`

---

## **9. 测试规范**

### **9.1 测试分层**

- `tests/api/`：接口契约测试
- `tests/services/`：业务逻辑测试
- `tests/repositories/`：存储层测试
- `tests/integration/`：与数据库、外部服务的集成测试

### **9.2 测试原则**

- 核心业务逻辑必须可脱离 HTTP 测试
- 外部依赖优先通过依赖覆盖替换
- 生命周期相关测试应覆盖 startup/shutdown 行为

### **9.3 必测内容**

- schema 校验
- 路由输入输出
- 鉴权失败路径
- 边界条件
- LLM 输出解析失败路径
- 第三方服务失败与重试路径

---

## **10. 工具链规范**

### **10.1 格式化与 Lint**

统一使用 Ruff：

- `ruff format`：格式化
- `ruff check`：lint

### **10.2 建议的最小检查项**

- 格式化检查
- lint 检查
- 单元测试
- 静态类型检查
- 可选：覆盖率门槛

### **10.3 pre-commit / CI**

建议在本地和 CI 都执行以下命令：

```
ruff format --check .
ruff check .
pytest
```

---

## **11. Mneme 项目专项规范**

### **11.1 Web API 与 Worker 分离**

Mneme 的 FastAPI 服务只负责：

- WebUI 查询接口
- 文章列表接口
- 摘要详情接口
- 健康检查
- 管理接口

定时抓取、总结、分类、IM 推送由独立 worker 执行。  
这样可以避免长任务污染 Web 服务的生命周期和响应延迟。

### **11.2 LLM 输出必须结构化**

OpenAI / Claude 的输出不得直接入库或直接发给前端。  
必须先映射为内部 Pydantic 模型，例如：

- `SummaryCard`
- `ClassificationResult`
- `DigestItem`

### **11.3 Source Adapter 规则**

每个内容源必须独立实现 adapter，并满足：

- 输入输出契约清晰
- 可单独测试
- 不在 adapter 内直接做总结
- 只负责抓取、解析、归一化

---

## **12. 禁止事项（Hard Rules）**

以下行为禁止进入主分支：

- 无类型标注的公共接口
- 在路由层直接写复杂业务逻辑
- 在业务代码中散落 `os.getenv()`
- 直接把第三方响应原样透传给前端
- 直接把 LLM 原始输出入库
- 以 `print()` 替代正式日志
- 未通过格式化、lint、测试即合并
- 用 `utils.py` 堆积杂项逻辑
- 大量复制粘贴相似 endpoint 或 service

---

## **13. 推荐的 `pyproject.toml` 方向**

```
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
ignore = []

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

---

## **14. 参考资料**

### **Python 官方**

- PEP 8：Python 代码风格指南
https://peps.python.org/pep-0008/
- PEP 257：Docstring 规范
https://peps.python.org/pep-0257/
- PEP 484：类型标注
https://peps.python.org/pep-0484/
- Logging HOWTO
https://docs.python.org/3/howto/logging.html

### **FastAPI 官方**

- FastAPI 总览
https://fastapi.tiangolo.com/
- Bigger Applications / APIRouter
https://fastapi.tiangolo.com/tutorial/bigger-applications/
- Response Model
https://fastapi.tiangolo.com/tutorial/response-model/
- Dependencies
https://fastapi.tiangolo.com/tutorial/dependencies/
- Settings and Environment Variables
https://fastapi.tiangolo.com/advanced/settings/
- Lifespan Events
https://fastapi.tiangolo.com/advanced/events/
- Testing / Testing Dependencies Overrides
https://fastapi.tiangolo.com/tutorial/testing/

### **Pydantic 官方**

- Models / Validation
https://docs.pydantic.dev/latest/concepts/models/
- Validators
https://docs.pydantic.dev/latest/concepts/validators/

### **Ruff 官方**

- Ruff 总览
https://docs.astral.sh/ruff/
- Ruff Linter
https://docs.astral.sh/ruff/linter/
- Ruff Formatter
https://docs.astral.sh/ruff/formatter/