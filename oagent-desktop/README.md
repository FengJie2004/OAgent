# OAgent Desktop

Tauri 桌面端应用，提供现代化的用户界面。

## 技术栈

- **Tauri 1.5** - Rust 后端 + WebView 前端
- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式
- **shadcn/ui** - UI 组件
- **Zustand** - 状态管理
- **TanStack Query** - 数据请求

## 开发

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run tauri:dev
```

### 构建

```bash
npm run tauri:build
```

## 项目结构

```
src/
├── components/      # React 组件
│   ├── layout/     # 布局组件
│   └── ui/         # UI 组件 (shadcn)
├── lib/           # 工具函数
├── pages/         # 页面组件
│   ├── Dashboard  # 仪表盘
│   ├── Chat       # 聊天界面
│   ├── Config     # 配置中心
│   └── Knowledge  # 知识库管理
├── services/      # API 服务
├── stores/        # Zustand 状态
├── types/         # TypeScript 类型
├── App.tsx        # 根组件
├── main.tsx       # 入口文件
└── index.css      # 全局样式

src-tauri/         # Tauri Rust 代码
├── src/
│   ├── main.rs    # 入口
│   └── lib.rs     # Tauri 命令
├── Cargo.toml     # Rust 依赖
└── tauri.conf.json # Tauri 配置
```

## 功能

### 已实现
- 基础布局和导航
- 聊天界面
- 配置管理界面
- 知识库管理界面
- 深色主题
- 状态持久化

### 待实现
- WebSocket 实时通信
- 流式响应
- 配置保存到后端
- 文件上传
- 系统托盘
- 自动更新

## 许可证

MIT License