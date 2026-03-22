# CopyHub

一个轻量级的多人协作剪贴板工具。

## 简介

CopyHub 是一个简洁高效的跨设备文本共享平台。打开网页即可看到一个文字列表，任何人都能往列表中新增数据，其他人也都能实时看见。主打轻量化，方便多人协作传递信息。

## 特性

- **轻量简洁** - 无需安装客户端，打开浏览器即可使用
- **多人协作** - 支持多人同时编辑，信息实时共享
- **跨设备同步** - 不同设备之间快速传递文本内容
- **一键部署** - 支持 Docker 快速部署

## 技术栈

- **前端**: Vue 3 + Vite + Tailwind CSS
- **后端**: FastAPI + SQLite
- **部署**: Docker + Nginx

## 项目结构

```
CopyHub/
├── frontend/          # Vue 3 前端项目
├── backend/           # FastAPI 后端项目
├── docker-compose.yml # Docker 编排文件
└── data/              # SQLite 数据持久化目录
```

## 快速开始

### Docker 一键部署

```bash
docker-compose up -d
```

访问 http://localhost 即可使用。

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

## License

MIT