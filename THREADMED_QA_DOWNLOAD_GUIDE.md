# ThReadMed-QA 数据集下载指南

## 📋 数据集信息

- **名称**: ThReadMed-QA
- **论文**: arXiv:2603.11281
- **GitHub**: https://github.com/monicamunnangi/ThReadMed-QA
- **数据量**: 2,437 个完整对话，8,204 个问答对
- **类型**: 真实多轮医患对话

## ⚠️ 当前状态

由于网络连接问题，自动下载失败。请使用以下方法手动下载。

---

## 📥 方法 1：使用 Git Clone（推荐）

### Windows (Git Bash)
```bash
cd data/raw/medical_dialogues/threadmed_qa
git clone https://github.com/monicamunnangi/ThReadMed-QA.git .
```

### Windows (PowerShell)
```powershell
cd data/raw/medical_dialogues/threadmed_qa
git clone https://github.com/monicamunnangi/ThReadMed-QA.git .
```

### Linux / macOS
```bash
cd data/raw/medical_dialogues/threadmed_qa
git clone https://github.com/monicamunnangi/ThReadMed-QA.git .
```

---

## 📥 方法 2：手动下载 ZIP

### 步骤：
1. 访问：https://github.com/monicamunnangi/ThReadMed-QA
2. 点击绿色的 "Code" 按钮
3. 点击 "Download ZIP"
4. 解压到：`data/raw/medical_dialogues/threadmed_qa/`

### Windows 解压命令：
```powershell
Expand-Archive -Path ThReadMed-QA-main.zip -DestinationPath data\raw\medical_dialogues\threadmed_qa\
```

### Linux / macOS 解压命令：
```bash
unzip ThReadMed-QA-main.zip -d data/raw/medical_dialogues/threadmed_qa/
```

---

## 📥 方法 3：使用下载脚本

### Windows (Git Bash / WSL)
```bash
bash download_threadmed_qa.sh
```

### Linux / macOS
```bash
bash download_threadmed_qa.sh
```

---

## 🔄 下载后：运行转换

### 1. 确认数据已下载
```bash
ls data/raw/medical_dialogues/threadmed_qa/
# 应该看到数据文件，如：data/, README.md 等
```

### 2. 运行转换脚本
```bash
python convert_threadmed_qa.py
```

### 3. 检查输出
```bash
ls -la data/tau2/domains/clinical/threadmed_qa/
# 应该看到：tasks.json, split_tasks.json 等
```

---

## 📊 预期结果

转换后的数据将存储在：
```
data/tau2/domains/clinical/threadmed_qa/
├── tasks.json              # 所有 2,437 个任务
├── tasks_train.json        # 训练集 (~1,950 任务)
├── tasks_val.json          # 验证集 (~244 任务)
├── tasks_test.json         # 测试集 (~243 任务)
└── split_tasks.json        # 数据划分
```

---

## 🆘 故障排除

### 问题 1：网络连接超时
**解决方案**：
- 稍后重试（可能是 GitHub 临时不可用）
- 使用 VPN 或代理
- 从其他设备下载后传输到本机

### 问题 2：仓库不存在（404 错误）
**解决方案**：
- 检查 GitHub 仓库是否存在
- 论文刚发布（2025年3月），代码可能还未上传
- 联系作者：monicamunnangi@gmail.com

### 问题 3：权限问题
**解决方案**：
- 确保你有 `data/raw/medical_dialogues/threadmed_qa/` 目录的写权限
- 在 Linux/macOS 上使用 `sudo`（如果有必要）

---

## 📞 获取帮助

如果遇到问题：
1. 查看 GitHub Issues：https://github.com/monicamunnangi/ThReadMed-QA/issues
2. 查看论文：https://arxiv.org/html/2603.11281v1
3. 检查网络连接：`ping github.com`

---

## 📅 下载检查清单

下载完成后，请确认：
- [ ] 文件已解压到正确位置
- [ ] 包含数据文件（JSON/CSV）
- [ ] `convert_threadmed_qa.py` 脚本可以运行
- [ ] 转换后 `data/tau2/domains/clinical/threadmed_qa/` 有文件

---

**创建日期**: 2025-03-13
**状态**: 待手动下载
