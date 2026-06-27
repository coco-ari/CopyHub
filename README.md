# CopyHub

一个轻量级的多人协作剪贴板工具，用浏览器在多台设备之间同步文本内容。

## 界面展示

![浅色模式](./img/ui1.png)
![深色模式](./img/ui2.png)

## 快速开始

### Docker 一键部署

```bash
docker compose up -d
```

访问 http://localhost:12500 即可使用。

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

前端访问地址: http://localhost:5173

如果后端没有运行在默认的 `127.0.0.1:8000`，可以指定代理地址:

```bash
VITE_BACKEND_URL=http://127.0.0.1:8001 npm run dev
```

生产构建:

```bash
cd frontend
npm run build
```

## 功能特性

- **实时同步** - 基于 WebSocket，多客户端消息实时更新
- **断线兜底** - WebSocket 重连后自动重新拉取数据，发送和修改成功后本地立即更新
- **内容修改** - 支持直接修改已保存的文本内容
- **容量控制** - 支持分页、最大内容长度限制和旧数据自动清理
- **深色模式** - 自动跟随系统，一键切换主题
- **轻量简洁** - 无需安装客户端，打开浏览器即可使用
- **跨设备同步** - 不同设备之间快速传递文本内容
- **一键部署** - 支持 Docker 快速部署

## 技术栈

| 类型 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Naive UI |
| 后端 | FastAPI + SQLite |
| 实时通信 | WebSocket |
| 部署 | Docker + Nginx |

## 配置项

后端支持通过环境变量调整运行策略:

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATA_DIR` | `./data` | SQLite 数据目录 |
| `DATABASE_URL` | `sqlite:///{DATA_DIR}/copyhub.db` | 数据库连接地址 |
| `MAX_CONTENT_LENGTH` | `10000` | 单条内容最大字符数 |
| `DEFAULT_ITEMS_LIMIT` | `100` | 列表接口默认返回条数 |
| `MAX_ITEMS_LIMIT` | `200` | 列表接口允许的最大返回条数 |
| `RETENTION_ITEMS` | `500` | 最多保留的内容条数，设为 `0` 表示不自动清理 |
| `BROADCAST_TIMEOUT_SECONDS` | `3` | WebSocket 单连接广播超时时间 |

前端开发服务器支持:

| 变量 | 说明 |
|------|------|
| `VITE_BACKEND_URL` | `/api` 代理目标，例如 `http://127.0.0.1:8001` |
| `VITE_BACKEND_WS_URL` | `/ws` 代理目标；不设置时由 `VITE_BACKEND_URL` 自动转换 |

## 项目结构

```text
CopyHub/
├── frontend/                # Vue 3 前端项目
│   ├── src/
│   │   ├── App.vue          # 主应用组件
│   │   └── components/      # 组件目录
│   ├── Dockerfile
│   └── nginx.conf           # Nginx 配置
├── backend/                 # FastAPI 后端项目
│   ├── main.py              # API 路由 + WebSocket
│   ├── models.py            # 数据模型
│   ├── database.py          # 数据库配置
│   └── Dockerfile
├── img/                     # 截图
├── docker-compose.yml       # Docker 编排文件
└── data/                    # SQLite 数据持久化目录
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/items?limit=100&offset=0` | 分页获取剪贴板内容，按时间倒序返回 |
| POST | `/api/items` | 新增剪贴板内容 |
| PUT | `/api/items/{id}` | 修改指定内容 |
| DELETE | `/api/items/{id}` | 删除指定内容 |
| WebSocket | `/ws` | 实时消息推送 |

WebSocket 消息类型:

| 类型 | 说明 |
|------|------|
| `create` | 新增内容 |
| `update` | 修改内容 |
| `delete` | 删除内容 |

## License

MIT
