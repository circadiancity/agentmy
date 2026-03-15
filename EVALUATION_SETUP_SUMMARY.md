# Tau2-Bench 评测设置完成

## ✅ 已完成的工作

### 1. 环境验证
- [x] Python 3.14.3 已安装
- [x] 虚拟环境已配置 (.venv)
- [x] Tau2-bench 依赖已安装
- [x] 临床数据已验证 (2,450 个任务)

### 2. 创建的文件

| 文件 | 用途 |
|------|------|
| `.env` | API 密钥配置文件 |
| `run_clinical_benchmark.py` | 完整的评测脚本 |
| `test_benchmark.ps1` | 环境测试脚本 |
| `CLINICAL_BENCHMARK_GUIDE.md` | 详细使用指南 |
| `cleanup_old_data.ps1` | 数据清理脚本 |
| `RESTRUCTURING_PLAN.md` | 项目重组计划 |

### 3. 更新的文件

| 文件 | 更新内容 |
|------|----------|
| `README.md` | 添加评测指南链接和快速开始指南 |

## 📋 临床域概览

| 临床域 | 任务数 | 描述 |
|--------|--------|------|
| clinical_cardiology | 758 | 心脏科 - 心血管疾病、心电图、血压 |
| clinical_endocrinology | 176 | 内分泌科 - 糖尿病、甲状腺、激素 |
| clinical_gastroenterology | 475 | 胃肠科 - 消化系统、肝脏、内镜 |
| clinical_nephrology | 300 | 肾病科 - 肾脏疾病、CKD 分期、透析 |
| clinical_neurology | 741 | 神经科 - 脑血管、癫痫、头痛 |
| **总计** | **2,450** | **5 个临床科室** |

## 🚀 开始运行评测

### 第一步：配置 API 密钥

编辑 `.env` 文件：

```bash
# 使用你选择的 API 密钥
OPENAI_API_KEY=sk-your-openai-api-key-here
# 或
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
```

### 第二步：运行测试评测

```bash
# 列出所有可用的临床域
python run_clinical_benchmark.py --list

# 运行单个任务测试（推荐先运行这个）
python run_clinical_benchmark.py --domain clinical_neurology --max-tasks 1 --max-rounds 1
```

### 第三步：运行完整评测

```bash
# 运行所有临床域（每个域 5 个任务）
python run_clinical_benchmark.py --all --max-tasks 5

# 运行单个临床域（10 个任务）
python run_clinical_benchmark.py --domain clinical_cardiology --max-tasks 10
```

## 📊 评测结果

结果保存在 `outputs/clinical/<domain>/` 目录：

```
outputs/
└── clinical/
    ├── clinical_neurology/
    │   └── result_20260311_234412.json
    ├── clinical_cardiology/
    │   └── result_20260311_234500.json
    └── ...
```

## 💰 成本估算

| 模型 | 每任务成本 | 10 个任务 | 100 个任务 |
|------|-----------|----------|-----------|
| GPT-3.5-turbo | ~$0.01 | $0.10 | $1.00 |
| GPT-4 | ~$0.10 | $1.00 | $10.00 |
| Claude 3 Opus | ~$0.15 | $1.50 | $15.00 |

*估算基于平均 3 轮对话*

## 📚 相关文档

- **详细指南**: [CLINICAL_BENCHMARK_GUIDE.md](CLINICAL_BENCHMARK_GUIDE.md)
- **项目总结**: [CLINICAL_DOMAINS_SUMMARY.md](CLINICAL_DOMAINS_SUMMARY.md)
- **GitHub 仓库**: https://github.com/circadiancity/agentmy

## 🎯 常用命令

```bash
# 测试环境
.\test_benchmark.ps1

# 列出所有临床域
python run_clinical_benchmark.py --list

# 单域测试
python run_clinical_benchmark.py --domain clinical_neurology --max-tasks 1

# 单域小规模评测
python run_clinical_benchmark.py --domain clinical_cardiology --max-tasks 5

# 所有域小规模评测
python run_clinical_benchmark.py --all --max-tasks 5

# 使用特定模型
python run_clinical_benchmark.py --domain clinical_neurology --agent-model gpt-3.5-turbo
```

## 🐛 遇到问题？

1. **API 密钥错误**: 检查 `.env` 文件是否正确配置
2. **模块导入错误**: 确保激活虚拟环境 `.venv\Scripts\activate`
3. **编码错误**: 使用 PowerShell 而非 CMD
4. **依赖缺失**: 运行 `pip install -e .`

## 📞 下一步

1. ✅ 配置 API 密钥
2. ✅ 运行测试评测 (`--max-tasks 1`)
3. ✅ 运行小规模评测 (`--max-tasks 5`)
4. ✅ 运行完整评测 (`--max-tasks 100`)

---

**创建日期**: 2026-03-11
**项目**: Tau2-Bench Clinical Domains
**仓库**: https://github.com/circadiancity/agentmy
