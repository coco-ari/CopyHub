# CopyHub Frontend

CopyHub 的前端应用，基于 Vue 3、Vite 和 Naive UI。

## 开发

```bash
npm install
npm run dev
```

默认会把 `/api` 和 `/ws` 代理到 `http://127.0.0.1:8000`。

如果后端运行在其他端口:

```bash
VITE_BACKEND_URL=http://127.0.0.1:8001 npm run dev
```

## 构建

```bash
npm run build
```

构建产物输出到 `dist/`。
