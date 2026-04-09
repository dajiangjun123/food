# 美团外卖AI推荐系统

## 项目简介

美团外卖AI推荐系统是一个基于深度学习算法的个性化菜品推荐服务，采用分层推荐架构，包括召回层、粗排层、精排层和重排层。

## 核心功能

- **数据采集与预处理**：用户行为数据、菜品特征数据的采集、清洗和标准化
- **用户画像构建**：基于用户行为数据的偏好模型构建和分群
- **推荐算法模型**：协同过滤、内容推荐、混合推荐等多种算法
- **实时推荐服务**：实时特征计算、性能优化、缓存机制
- **A/B测试框架**：多策略并行测试、实验配置、效果分析
- **健康检查API**：系统监控、性能指标、缓存管理

## 技术栈

- **后端**：Python/FastAPI
- **数据库**：MongoDB、Redis
- **消息队列**：Kafka
- **机器学习**：TensorFlow/PyTorch
- **部署**：Vercel

## 快速开始

### 本地开发

1. **克隆项目**
   ```bash
   git clone https://github.com/dajiangjun123/food.git
   cd food
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，配置相关参数
   ```

4. **启动开发服务器**
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **访问API文档**
   - API文档：http://localhost:8000/docs
   - 健康检查：http://localhost:8000/health

### Vercel部署

1. **连接GitHub仓库**
   - 登录Vercel账号
   - 点击"New Project"
   - 选择GitHub仓库 `dajiangjun123/food`

2. **配置部署**
   - 框架：Python
   - 根目录：`/`
   - 构建命令：`pip install -r requirements.txt`
   - 启动命令：`uvicorn app.main:app --host 0.0.0.0 --port 8000`

3. **配置环境变量**
   - 在Vercel项目设置中添加环境变量
   - 参考 `.env.example` 文件

4. **部署项目**
   - 点击"Deploy"按钮
   - 等待部署完成

## API接口

### 1. 用户行为数据
- `POST /api/user-behaviors` - 采集用户行为数据
- `GET /api/user-behaviors/{user_id}` - 获取用户行为历史

### 2. 菜品特征
- `POST /api/dish-features` - 创建菜品特征
- `GET /api/dish-features/{dish_id}` - 获取菜品特征

### 3. 用户画像
- `POST /api/user-profiles` - 创建用户画像
- `GET /api/user-profiles/{user_id}` - 获取用户画像

### 4. 推荐服务
- `POST /api/recommendations` - 获取智能推荐

### 5. A/B测试
- `POST /api/ab-test/experiments` - 创建实验
- `POST /api/ab-test/experiments/{experiment_id}/start` - 启动实验
- `POST /api/ab-test/experiments/{experiment_id}/assign/{user_id}` - 用户分组分配
- `GET /api/ab-test/experiments/{experiment_id}/analysis` - 分析实验结果

### 6. 健康检查
- `GET /health` - 健康检查
- `GET /api/health/metrics` - 获取性能指标

## 项目结构

```
.
├── app/
│   ├── api/          # API接口
│   ├── core/         # 核心配置
│   ├── models/       # 数据模型
│   ├── services/     # 业务逻辑
│   └── main.py       # 应用入口
├── tests/            # 测试代码
├── logs/             # 日志文件
├── .env.example      # 环境变量示例
├── requirements.txt  # 依赖配置
├── vercel.json       # Vercel配置
└── Procfile          # 启动配置
```

## 测试

运行测试套件：

```bash
python -m pytest tests/
```

## 许可证

MIT License
