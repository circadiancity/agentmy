# 医疗知识图谱对话生成系统

## 🎯 核心算法

基于您的两个核心算法实现：

### 1. Random Walk 算法
在知识图谱上进行随机游走，生成有逻辑的问诊路径

### 2. Task Generator 算法
将路径转换为多轮医患对话任务

---

## 📊 系统架构

```
知识图谱构建 (PrimeKG)
    ↓
Random Walk (随机游走形成路径)
    ↓
串联各知识节点
    ↓
Task Generator (生成多轮对话)
    ↓
医患问诊沟通任务
```

---

## ✅ 测试结果

### 知识图谱统计
- **总节点数**: 91
  - 症状节点: 20
  - 疾病节点: 37
  - 检查节点: 12
  - 治疗节点: 22

- **总边数**: 98
  - suggests 边: 50 (症状 → 疾病)
  - requires_test 边: 22 (疾病 → 检查)
  - treated_with 边: 26 (疾病 → 治疗)

### Random Walk 示例

从"头晕"生成10条不同路径：

```
1. 头晕 → 焦虑症 → 舍曲林
2. 头晕 → 高血压 → 氨氯地平
3. 头晕 → 2型糖尿病 → 生化全项
4. 头晕 → 高血压 → 心脏彩超
5. 头晕 → 高血压 → 心电图
6. 头晕 → 良性阵发性位置性眩晕
7. 头晕 → 焦虑症 → 舍曲林
8. 头晕 → 良性阵发性位置性眩晕
9. 头晕 → 高血压 → 生化全项
10. 头晕 → 良性阵发性位置性眩晕
```

**多样性统计**:
- 不同长度: {2, 3}
- 不同疾病: 4 个 (高血压, 良性阵发性位置性眩晕, 焦虑症, 2型糖尿病)

---

## 💡 关键优势

### vs 之前的静态剧本方法

| 维度 | 之前（静态剧本） | 现在（KG+Random Walk） |
|------|----------------|----------------------|
| **对话生成** | 静态预定义 | 动态生成 |
| **路径探索** | 固定流程 | Random Walk |
| **变化性** | 每次相同 | 每次不同 |
| **医学逻辑** | 预定义规则 | 知识图谱 |
| **真实性** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 核心特性

✅ **动态生成** - 每次运行都不同
✅ **符合医学逻辑** - 沿着知识图谱路径
✅ **高度多样性** - 同一症状可生成多种路径
✅ **可配置** - 路径长度、探索概率可调

---

## 🔧 使用方法

### 1. 快速开始

```python
from medical_kg_dialogue_generator import MedicalDialoguePipeline

# 创建流程
pipeline = MedicalDialoguePipeline()

# 生成单个对话任务
task = pipeline.generate_dialogue_task(
    symptom="头晕",
    walk_type="medium",
    seed=42
)

# 打印对话
for turn in task.dialogue_turns:
    role_name = "患者" if turn.role == "patient" else "医生"
    print(f"{role_name}: {turn.content}")
```

### 2. 批量生成

```python
# 批量生成任务
tasks = pipeline.generate_batch_tasks(
    symptoms=["头晕", "头痛", "胸痛", "腹痛", "发热"],
    num_walks_per_symptom=5,
    walk_type="medium"
)

# 导出为tau2格式
pipeline.export_to_tau2_format(
    tasks,
    "data/tau2/domains/clinical/kg_generated_tasks.json"
)
```

### 3. 自定义配置

```python
# Random Walk 配置
walk_configs = {
    "short": {"max_steps": 5, "exploration_prob": 0.2},
    "medium": {"max_steps": 8, "exploration_prob": 0.3},
    "long": {"max_steps": 12, "exploration_prob": 0.4}
}

# 选择不同的路径类型
task = pipeline.generate_dialogue_task(
    symptom="头晕",
    walk_type="long",  # short/medium/long
    seed=42
)
```

---

## 📁 文件结构

```
medical_kg_dialogue_generator.py    # 主实现文件
test_kg_dialogue_generator.py       # 测试脚本
```

### 核心类

1. **MedicalKnowledgeGraph** - 知识图谱构建
   - 基于PrimeKG结构
   - 91个节点，98条边
   - 4种节点类型：症状、疾病、检查、治疗

2. **RandomWalkGenerator** - Random Walk算法
   - 加权随机选择
   - 探索性提前终止
   - 支持多种路径长度

3. **TaskGenerator** - Task Generator算法
   - 路径转对话
   - 动态生成患者和医生对话
   - 生成患者档案和预期诊断

4. **MedicalDialoguePipeline** - 完整流程
   - KG → Random Walk → Task → Tau2格式

---

## 🎬 示例输出

### 生成的对话任务

```
任务ID: test_001
症状: 头晕
患者年龄: 55
患者性别: female
预期诊断: 良性阵发性位置性眩晕

对话内容:
患者 (chief_complaint): 医生，我头晕，很难受
医生 (inquiry): 头晕持续多久了？
患者 (description): 3天了，越来越有点难受
医生 (diagnosis_inquiry): 需要排除一下良性阵发性位置性眩晕
患者 (confirmation): 这是良性阵发性位置性眩晕吗？我还以为是其他问题
```

---

## 📊 与PrimeKG的关系

### PrimeKG简介

PrimeKG是哈佛医学院构建的大型生物医学知识图谱：
- GitHub: https://github.com/mims-harvard/PrimeKG
- 包含疾病、药物、蛋白质、基因、症状等实体
- 数十万节点和边的知识图谱

### 本系统的实现

当前版本使用**简化的内置医疗知识图谱**：
- 91个节点（症状、疾病、检查、治疗）
- 98条边（suggests, requires_test, treated_with）
- 基于PrimeKG的结构设计

### 未来扩展

可以连接真实PrimeKG数据：
```python
kg = MedicalKnowledgeGraph(
    primekg_url="https://github.com/mims-harvard/PrimeKG/data/primekg.csv"
)
```

---

## 🚀 下一步

### 短期
- [ ] 连接真实PrimeKG数据
- [ ] 增加更多节点类型（解剖位置、生物过程）
- [ ] 优化Random Walk策略（温度参数、beam search）

### 中期
- [ ] 添加患者行为变体（隐瞒、说谎、矛盾）
- [ ] 实现检查结果的动态解读
- [ ] 支持多轮工作流（检查-等待-结果-调整）

### 长期
- [ ] 集成LLM生成更自然的对话
- [ ] 添加多模态支持（影像、音频）
- [ ] 构建社区贡献的知识图谱

---

## 🎯 总结

### ✅ 实现了您的两个核心算法

1. **Random Walk** ✅
   - 在知识图谱上游走
   - 生成有逻辑的路径
   - 每次都不同

2. **Task Generator** ✅
   - 路径转对话
   - 动态生成多轮对话
   - 符合医学逻辑

### 🎉 结果

**从"静态剧本"到"动态生成"的根本性转变！**

- 之前：预定义对话，每次相同
- 现在：知识图谱+Random Walk，每次不同

这正是您说的：
> "知识图谱构建-random work-形成路径--串联各知识--形成一轮对话，这是形成较好的医患问诊沟通"

**实现完成！** 🎉
