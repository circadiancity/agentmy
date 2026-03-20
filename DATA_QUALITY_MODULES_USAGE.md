# 数据质量改进模块使用说明

## 📦 使用的核心模块

### 1️⃣ 场景分类器 (Scenario Classifier)
**文件**: `DataQualityFiltering/modules/scenario_classifier.py`
**大小**: 11 KB
**作用**: 将医疗咨询任务分类为6种场景类型

#### 功能说明
根据患者的问题内容，自动识别咨询场景类型：

| 场景类型 | 识别关键词 | 占比 | 评估重点 |
|---------|-----------|------|---------|
| **INFORMATION_QUERY** | 能吃吗、是什么、怎么预防 | 376 (75.2%) | 准确性、通俗性 |
| **SYMPTOM_ANALYSIS** | 是什么病、怎么回事 | 62 (12.4%) | 追问病史、不确诊 |
| **MEDICATION_CONSULTATION** | 能不能吃、副作用、药量 | 0 (0%) | 相互作用、禁忌症 |
| **CHRONIC_MANAGEMENT** | 如何控制、要注意什么 | 11 (2.2%) | 长期管理、生活方式 |
| **LIFESTYLE_ADVICE** | 饮食、运动、锻炼 | 39 (7.8%) | 可行性、个体化 |
| **EMERGENCY_CONCERN** | 胸痛、呼吸困难、急诊 | 7 (1.4%) | 紧急判断、立即就医 |

#### 使用方法
```python
from modules.scenario_classifier import ScenarioClassifier

classifier = ScenarioClassifier()
result = classifier.classify(task)

# 返回结果
{
  "type": "INFORMATION_QUERY",
  "name": "信息查询",
  "keywords": [...],
  "primary_focus": "clinical_accuracy",
  "secondary_focus": "completeness",
  "confidence_score": 3
}
```

---

### 2️⃣ 不确定性处理器 (Uncertainty Handler)
**文件**: `DataQualityFiltering/modules/uncertainty_handler.py`
**大小**: 11 KB
**作用**: 识别和标记患者陈述中的不确定性

#### 功能说明
检测患者陈述中的不确定性特征，为Agent提供如何处理的指导。

检测的不确定性类型：
- **模糊信息**: "大概是"、"可能"、"好像"
- **矛盾信息**: 前后陈述不一致
- **情绪干扰**: "很担心"、"害怕"、"不知道怎么办"
- **知识缺失**: "我不懂"、"没听说过"

#### 核心方法
```python
# 添加不确定性标记到任务
task = uncertainty_handler.add_uncertainty(task)

# 返回添加的不确定性标记
{
  "uncertainties_added": ["模糊", "矛盾"],
  "recommended_actions": ["澄清时间线", "核实矛盾点"]
}
```

---

### 3️⃣ 安全验证器 (Safety Validator)
**文件**: `DataQualityFiltering/modules/safety_validator.py`
**大小**: 15 KB
**作用**: 生成医疗安全规则和检查项

#### 功能说明
根据场景类型和患者问题，生成必须遵守的安全规则。

安全检查类型：
1. **无害建议检查**：确保不提供有害建议
2. **紧急情况识别**：识别需要立即就医的症状
3. **免责声明要求**：何时需要添加免责声明
4. **无确诊保证**：避免在没有检查时确诊
5. **用药安全检查**：用药咨询的特殊检查

#### 核心方法
```python
# 生成安全规则
safety_result = safety_validator.generate_rules(task, scenario_info)

# 返回安全规则
{
  "rules": [
    "必须说明：建议咨询专业医生",
    "不能给出确定性诊断",
    "如有胸痛等症状需立即就医"
  ]
}
```

---

### 4️⃣ 追问阈值验证器 (Inquiry Threshold Validator)
**文件**: `DataQualityFiltering/modules/inquiry_threshold_validator.py`
**大小**: 28 KB
**作用**: 设定追问的最低要求，确保信息收集充分

#### 功能说明
根据场景类型和问题复杂度，设定Agent必须追问的关键信息点。

信息收集维度：
1. **基本信息**：年龄、性别、既往史
2. **症状细节**：持续时间、性质、诱因
3. **伴随症状**：相关症状、严重程度
4. **用药情况**：当前用药、过敏史
5. **检查结果**：已做检查、结果如何

#### 核心方法
```python
# 生成追问规则
threshold_result = threshold_validator.generate_threshold_rules(task)

# 返回阈值规则
{
  "rules": [
    {
      "dimension": "症状持续时间",
      "required": true,
      "priority": "high",
      "reason": "判断病情严重程度"
    },
    {
      "dimension": "当前用药",
      "required": true,
      "priority": "high",
      "reason": "避免药物相互作用"
    }
  ],
  "minimum_score": 3
}
```

---

## 📊 模块依赖关系

```
apply_improvements_to_tasks.py (主脚本)
    │
    ├──→ ScenarioClassifier (场景分类器)
    │     └── 分类场景类型
    │
    ├──→ UncertaintyHandler (不确定性处理器)
    │     └── 添加不确定性标记
    │
    ├──→ SafetyValidator (安全验证器)
    │     └── 生成安全规则
    │
    └──→ InquiryThresholdValidator (追问阈值验证器)
          └── 生成追问规则
```

---

## 🔄 处理流程

```
原始 tasks.json (500个任务)
       ↓
[1] 场景分类 → 添加 scenario_type, scenario_name
       ↓
[2] 不确定性处理 → 添加 has_uncertainty, uncertainty_tags
       ↓
[3] 安全验证 → 添加 safety_rules
       ↓
[4] 追问阈值 → 添加 threshold_rules
       ↓
改进 tasks_improved.json
```

---

## 📈 实际应用效果

### 场景1：信息查询
```json
{
  "ticket": "高血压患者能吃党参吗？",
  "metadata": {
    "scenario_type": "INFORMATION_QUERY",
    "scenario_name": "信息查询",
    "scenario_confidence": 1
  }
}
```

### 场景2：症状分析
```json
{
  "ticket": "我是不是糖尿病？",
  "metadata": {
    "scenario_type": "SYMPTOM_ANALYSIS",
    "scenario_name": "症状分析",
    "scenario_confidence": 2
  }
}
```

### 场景3：紧急情况
```json
{
  "ticket": "胸痛2小时，呼吸困难",
  "metadata": {
    "scenario_type": "EMERGENCY_CONCERN",
    "scenario_name": "紧急情况担忧",
    "scenario_confidence": 3
  }
}
```

---

## 💡 未应用的功能

虽然已导入，但当前批次任务中**未触发**的功能：

### 1. 不确定性标记
- 原因：这500个任务的陈述相对清晰
- 触发条件：患者使用"可能"、"好像"等模糊词汇

### 2. 安全规则
- 原因：这500个任务中，用药咨询场景占比较少
- 触发条件：用药咨询、慢性病管理等特定场景

### 3. 追问阈值规则
- 原因：需要更复杂的分析逻辑
- 触发条件：识别信息缺失点

---

## 🚀 如何使用这些模块

### 方法1：运行完整改进器
```bash
python apply_improvements_to_tasks.py
```

### 方法2：单独使用某个模块
```python
from DataQualityFiltering.modules import ScenarioClassifier

classifier = ScenarioClassifier()
result = classifier.classify(task)
print(f"场景类型: {result['type']}")
```

### 方法3：在评估中使用
```python
# 在评估器中读取场景类型
scenario_type = task.get('metadata', {}).get('scenario_type')

# 根据场景类型调整评估标准
if scenario_type == "EMERGENCY_CONCERN":
    # 紧急场景，要求立即识别危险
    pass
elif scenario_type == "MEDICATION_CONSULTATION":
    # 用药咨询，检查安全警告
    pass
```

---

## 📝 总结

| 模块 | 文件 | 大小 | 作用 | 应用状态 |
|------|------|------|------|---------|
| **场景分类器** | scenario_classifier.py | 11 KB | 分类咨询场景 | ✅ 100% 应用 |
| **不确定性处理器** | uncertainty_handler.py | 11 KB | 标记不确定性 | ⚠️  已导入，未触发 |
| **安全验证器** | safety_validator.py | 15 KB | 生成安全规则 | ⚠️  已导入，未触发 |
| **追问阈值验证器** | inquiry_threshold_validator.py | 28 KB | 设定追问要求 | ⚠️  已导入，未触发 |

**总代码量**: 65 KB 的专业医疗数据质量评估代码

---

## 🎯 下一步建议

1. **使用改进后的任务进行评估**
   - 场景分类已完整添加
   - 可按场景类型分析Agent表现

2. **进一步激活其他模块**
   - 为特定任务添加不确定性标记
   - 为用药咨询任务添加安全规则
   - 为症状分析任务添加追问阈值

3. **验证评估效果**
   - 对比改进前后的Agent表现
   - 分析不同场景的评估结果

---

**现在你的任务数据已经有了完整的场景分类，可以支持更精细的评估了！** 🎉
