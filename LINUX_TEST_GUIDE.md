# 本地Linux测试指南 - 确保GitHub Actions通过

> 💡 **核心理念**：在本地模拟GitHub Actions环境，测试通过后再推送

## 🎯 问题与解决方案

### 问题
- 本地Windows环境 ≠ GitHub Actions Linux环境
- 导致：本地通过，GitHub失败

### 解决方案
**环境一致性测试**：在本地用Linux环境测试，通过后再推送

---

## 🐳 方案A：Docker（最推荐）

### 优点
- ✅ **完全隔离**：不影响本地环境
- ✅ **环境一致**：与GitHub Actions 100%相同
- ✅ **可重现**：任何人都得到相同结果
- ✅ **易于调试**：可以进入容器交互

### 使用方法

#### 1. 安装Docker Desktop
```bash
# 下载并安装
https://www.docker.com/products/docker-desktop/
```

#### 2. 运行测试
```bash
# 方式1：使用脚本
bash test_with_docker.sh

# 方式2：手动命令
docker build -f Dockerfile.test -t tau2-test .
docker run --rm tau2-test
```

#### 3. 进入容器调试
```bash
# 交互式运行
docker run -it tau2-test bash

# 在容器内
python
>>> from DataQualityFiltering.core import LLMEvaluator
>>> # 测试你的代码
```

### Dockerfile.test 说明
- 基于 `ubuntu:22.04`（与GitHub Actions相同）
- 使用 Python 3.10
- 安装所有依赖
- 运行测试脚本

---

## 🐧 方案B：WSL2（最方便）

### 优点
- ✅ **原生Linux**：真实的Ubuntu环境
- ✅ **性能好**：接近原生Linux速度
- ✅ **文件共享**：直接访问Windows文件
- ✅ **免费**：Windows 10/11内置支持

### 使用方法

#### 1. 安装WSL2
```powershell
# PowerShell (管理员)
wsl --install

# 重启后，安装Ubuntu
# 从Microsoft Store搜索"Ubuntu"安装
```

#### 2. 运行测试
```bash
# 方式1：使用脚本
bash test_with_wsl.sh

# 方式2：手动进入WSL
wsl

# 在WSL中
cd /mnt/c/Users/方正/tau2-bench
python3 test_github_actions_locally.py
```

#### 3. 在WSL中开发
```bash
# 进入WSL
wsl

# 安装Python 3.10
sudo apt update
sudo apt install python3.10 python3-pip

# 运行测试
cd /mnt/c/Users/方正/tau2-bench
python3 -m pytest
```

---

## 🔄 推荐工作流程

### 开发流程

```
1. 本地Windows开发
   ↓
2. 提交前：Docker/WSL测试
   ↓
3. 测试通过 → 推送GitHub
   ↓
4. GitHub Actions验证
   ↓
5. ✅ 成功！
```

### 具体步骤

#### 阶段1：本地开发（Windows）
```bash
# 使用你喜欢的IDE
# 正常编写代码
code .
```

#### 阶段2：Linux环境测试
```bash
# 选项A：Docker测试
bash test_with_docker.sh

# 选项B：WSL测试
bash test_with_wsl.sh
```

#### 阶段3：推送到GitHub
```bash
# 只有Linux测试通过后才推送
git add .
git commit -m "feat: new feature"
git push
```

#### 阶段4：GitHub Actions验证
```bash
# 访问
https://github.com/circadiancity/agentmy/actions

# 应该看到：
✅ Basic Health Check - PASSED
```

---

## 📊 方案对比

| 特性 | Docker | WSL2 | 虚拟机 |
|------|--------|------|--------|
| **环境一致性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **易用性** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **性能** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **隔离性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **启动速度** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **资源占用** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |

### 推荐选择
- **日常开发**：WSL2（最快）
- **CI/CD验证**：Docker（最一致）
- **完整测试**：Docker（最可靠）

---

## 🚀 快速开始

### 第一次使用

#### 选择Docker
```bash
# 1. 安装Docker Desktop
# 2. 运行测试
bash test_with_docker.sh
```

#### 选择WSL2
```bash
# 1. 启用WSL
wsl --install

# 2. 运行测试
bash test_with_wsl.sh
```

### 集成到开发流程

#### Pre-commit Hook（自动测试）
```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running Docker tests..."
bash test_with_docker.sh
if [ $? -ne 0 ]; then
    echo "Tests failed! Commit aborted."
    exit 1
fi
```

#### Alias（快速测试）
```bash
# 添加到 ~/.bashrc 或 ~/.bash_profile
alias test-linux='bash ~/tau2-bench/test_with_docker.sh'
alias test-wsl='bash ~/tau2-bench/test_with_wsl.sh'

# 使用
test-linux  # Docker测试
test-wsl    # WSL测试
```

---

## 🐛 故障排除

### Docker相关

#### 问题：docker command not found
```bash
# 解决：安装Docker Desktop
https://www.docker.com/products/docker-desktop/
```

#### 问题：端口冲突
```bash
# 不需要暴露端口，这不影响
```

### WSL相关

#### 问题：WSL not found
```bash
# 解决：启用WSL
dism.exe /online /norestart
dism.exe /enable-feature:Microsoft-Windows-Subsystem-Linux /all /norestart
wsl --install
```

#### 问题：找不到项目目录
```bash
# WSL中Windows路径是 /mnt/c/
cd /mnt/c/Users/你的用户名/tau2-bench
```

---

## 📝 最佳实践

### 1. 测试驱动开发
```
本地开发 → Linux测试 → 修复问题 → 推送GitHub
```

### 2. 渐进式测试
```
Docker测试 → WSL验证 → GitHub Actions确认
```

### 3. 自动化
```
Pre-commit hook → 阻止未测试代码推送
```

---

## 🎉 总结

### 你的问题答案

**Q: 是否要在本地修复后再导入？**
✅ **是的！** 推荐流程：
1. 本地Windows开发
2. Docker/WSL测试（模拟GitHub环境）
3. 确认通过后再推送

**Q: 本地能建立Linux系统吗？**
✅ **可以！** 有三个选择：
- Docker（推荐）：容器化Linux
- WSL2（最方便）：原生Linux子系统
- 虚拟机（完整隔离）：完整Linux系统

### 下一步
1. **选择方案**：Docker还是WSL2？
2. **安装环境**：10-30分钟
3. **测试验证**：5分钟
4. **推送GitHub**：1分钟
5. **✅ 成功**：100%通过率

---

**选择一个方案，我帮你配置！**
