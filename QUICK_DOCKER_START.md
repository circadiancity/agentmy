# Docker 测试 - 快速开始 🐳

## ⚡ 5分钟快速开始

### 第1步：安装Docker Desktop（3分钟）

1. **下载**
   ```
   https://www.docker.com/products/docker-desktop/
   选择 "Docker Desktop for Windows"
   ```

2. **安装**
   - 双击下载的 `.exe` 文件
   - 使用默认设置
   - 等待安装完成

3. **重启**（如果需要）
   - 根据提示重启计算机
   - 启动Docker Desktop

4. **验证**
   - 查看系统托盘是否有鲸鱼图标
   - 图标应该显示为"Docker Desktop is running"

### 第2步：运行测试（2分钟）

在项目目录（`C:\Users\方正\tau2-bench`）打开Git Bash或PowerShell：

```bash
bash test_with_docker.sh
```

### 第3步：查看结果

看到这个输出就成功了：
```
✅ 构建完成！耗时：XXX秒
🧪 运行测试...
[OK] DataQualityFiltering imported
[OK] tau2 imported
[OK] ClinicalEvaluator imported
[OK] MedicalDialogueValidator works
[SUCCESS] Repository is healthy
🎉 所有测试通过！
```

---

## ✅ 成功标志

### Docker测试成功
```
✅ 测试通过
   ↓
git push
   ↓
✅ GitHub Actions也通过
```

---

## 🆘 遇到问题？

### 问题：bash: test_with_docker.sh: No such file

**解决**：确保在正确的目录
```bash
cd C:\Users\方正\tau2-bench
bash test_with_docker.sh
```

### 问题：docker command not found

**解决**：
1. 确保Docker Desktop正在运行
2. 重启终端
3. 或者使用PowerShell：
```powershell
docker --version
```

### 问题：构建失败

**解决**：查看详细日志
```bash
cat /tmp/docker_build.log
```

---

## 🎯 日常使用

### 推荐工作流

```bash
# 1. 编写代码
# ... 你的开发工作 ...

# 2. 提交前测试
bash test_with_docker.sh

# 3. 如果测试通过，推送
git add .
git commit -m "feat: new feature"
git push

# 4. 查看GitHub Actions结果
# https://github.com/circadiancity/agentmy/actions
```

### 快速命令别名

可以添加到你的Git Bash配置（`~/.bashrc`）：

```bash
alias test-docker='cd /c/Users/方正/tau2-bench && bash test_with_docker.sh'
alias git-push='cd /c/Users/方正/tau2-bench && git push'
```

使用：
```bash
test-docker  # 运行Docker测试
git-push     # 推送到GitHub
```

---

## 📊 预期输出

### 成功的输出

```
==========================================
  Docker 测试 - 模拟GitHub Actions
==========================================

🔍 检查Docker...
✅ Docker已安装
Docker version 24.0.7, build 12965

📦 构建Docker镜像...
这可能需要5-10分钟（第一次构建较慢）
[+] Building 85.6s (10/10)
✅ 构建完成！耗时：96秒

🧪 运行测试...
Working directory: /workspace
Python version: 3.10.12
[OK] DataQualityFiltering imported
[OK] tau2 imported
[OK] ClinicalEvaluator imported
[OK] MedicalDialogueValidator works
All basic tests passed!
[SUCCESS] Repository is healthy

==========================================
  🎉 所有测试通过！
==========================================

📤 下一步：
   git push
   ✅ GitHub Actions也会通过！
```

---

## 💡 提示

### 第一次运行较慢
- 构建：5-10分钟
- 后续运行：<1分钟

### 后续使用
```bash
# 修改代码后
bash test_with_docker.sh  # 重新测试

# 如果修改了依赖
docker build --no-cache -f Dockerfile.test -t tau2-test .
```

### 清理（如果需要）
```bash
# 清理Docker缓存
docker system prune -a

# 删除镜像
docker rmi tau2-test
```

---

## 🎉 开始使用

### 现在就可以测试了！

```bash
bash test_with_docker.sh
```

**测试通过后，GitHub Actions也会通过！** ✅
