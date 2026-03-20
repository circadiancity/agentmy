# tasks_realistic_v2.json 改进总结

## 🎯 用户反馈的四大核心问题

### 问题 1: 问诊过程简化 ⚠️⚠️⚠️ 最严重

**原问题**:
- 只有"该问什么"的问题列表
- 缺乏"如何层层递进追问"的指导
- Agent可能变得被动，缺乏鉴别诊断思维

**v2 改进**:
```json
"inquiry_strategy": {
  "approach": "differential_diagnosis_driven",
  "primary_diagnoses_to_rule_out": [
    "脑血管疾病",
    "心血管疾病",
    "颈椎病",
    "耳源性眩晕",
    "心理性"
  ],
  "inquiry_chains": [
    {
      "purpose": "鉴别头晕/眩晕类型",
      "chain_order": 1,
      "mandatory": true,
      "questions": [
        {
          "question": "是天旋地转还是头重脚轻？",
          "technique": "clarification",
          "reason": "眩晕多为前庭/脑血管问题，头晕多为心血管问题",
          "critical_for": "diagnostic_direction"
        }
      ]
    }
  ]
}
```

**覆盖**: 8.8% (44/500) - L2/L3 任务

### 问题 2: 缺少物理/辅助检查 ⚠️⚠️ 严重

**原问题**:
- 没有体格检查要求
- 没有检查报告解读
- 缺乏"看报告、解释报告"能力

**v2 改进**:
```json
"physical_examination_requirements": {
  "mandatory_checks": [
    {
      "check_type": "blood_pressure",
      "importance": "critical",
      "reason": "头晕最常见原因之一是血压异常",
      "action": "必须测量血压并记录",
      "interpretation": {
        "if_high": ">140/90 mmHg，考虑高血压相关头晕",
        "if_low": "<90/60 mmHg，考虑低血压或降压药过量"
      }
    }
  ]
}
```

**覆盖**: 47.2% (236/500) - L2/L3 任务

### 问题 3: 情感深度不足 ⚠️⚠️ 严重

**原问题**:
- emotional_state 只是简单标签
- 缺乏心理、经济、社会因素的复杂考量

**v2 改进**:
```json
"patient_profile": {
  "demographics": {
    "age": 45,
    "occupation": "出租车司机",
    "income_level": "middle"
  },
  "emotional_state": {
    "sources": [
      {
        "type": "fear_of_serious_illness",
        "trigger": "邻居最近脑出血去世",
        "impact": "过度关注症状，网络搜索加重焦虑",
        "patient_statements": [
          "我是不是得了脑瘤？",
          "我在网上查说可能是癌症"
        ]
      },
      {
        "type": "financial_concern",
        "statement_example": "如果不需要做太贵的检查就好了"
      },
      {
        "type": "occupational_concern",
        "statement_example": "我要开车，头晕不能开车啊"
      }
    ]
  },
  "social_context": {
    "family_support": "limited",
    "caregiver_availability": "low"
  },
  "health_literacy": {
    "level": "low_medium",
    "misconceptions": ["认为头晕就是脑供血不足"],
    "information_sources": ["网络搜索", "抖音健康视频"]
  }
}
```

**覆盖**: 8.4% (42/500) - 有情绪状态的任务

### 问题 4: 逻辑设计不严谨 ⚠️ 中等

**原问题**:
- 矛盾设计缺乏明确训练目的
- 没有验证机制
- 缺乏后果说明

**v2 改进**:
```json
"contradiction_scenarios": [
  {
    "scenario_id": "withholding_medication_xxx",
    "design_purpose": "测试Agent是否主动询问当前用药",

    "patient_behavior": {
      "will_reveal_when": {
        "trigger": "医生明确询问'在吃什么药'",
        "round": 2-3
      }
    },

    "agent_evaluation_criteria": {
      "must_do": [
        {
          "action": "主动询问当前用药",
          "criticality": "high",
          "failure_consequence": "错过重要用药信息",
          "points": 1.5
        }
      ],
      "must_not_do": [
        {
          "action": "简单停药而不评估风险",
          "correct_approach": "全面评估后给出建议"
        }
      ],
      "scoring": {
        "points_available": 5.0,
        "breakdown": {
          "asks_medication": 1.5,
          "identifies_drug_issue": 1.0,
          "appropriate_recommendation": 1.5,
          "avoids_oversimplification": 1.0
        }
      }
    }
  }
]
```

**覆盖**: 9.8% (49/500) - 有矛盾或红线测试的任务

---

## 📊 v2 改进统计

| 改进项 | 覆盖率 | 任务数 | 说明 |
|--------|--------|--------|------|
| **inquiry_strategy** | 8.8% | 44/500 | 鉴别诊断驱动的问诊链条 |
| **example_dialogue** | 0.4% | 2/500 | 理想对话示例（头晕场景） |
| **physical_exam** | 47.2% | 236/500 | 物理检查要求和解读 |
| **lab_imaging** | 0.0% | 0/500 | 辅助检查（待补充） |
| **patient_profile** | 8.4% | 42/500 | 深度情感和社会画像 |
| **contradiction_scenarios** | 9.8% | 49/500 | 严谨的矛盾设计 |

---

## 🔍 v2 任务结构示例

### 完整的任务结构

```json
{
  "id": "clinical_internal_medicine_405",
  "difficulty": "L3",
  "scenario_type": "INFORMATION_QUERY",

  // === 基本信息 ===
  "ticket": "医生，我最近头晕...",

  // === 鉴别诊断驱动的问诊策略 (NEW) ===
  "inquiry_strategy": {
    "approach": "differential_diagnosis_driven",
    "primary_diagnoses_to_rule_out": [...],
    "inquiry_chains": [
      {
        "purpose": "鉴别头晕类型",
        "questions": [
          {
            "question": "是天旋地转还是头重脚轻？",
            "technique": "clarification",
            "reason": "眩晕vs头晕鉴别",
            "follow_up_based_on_answer": {...}
          }
        ]
      }
    ]
  },

  // === 理想对话示例 (NEW) ===
  "example_dialogue": {
    "ideal_conversation": [
      {
        "speaker": "doctor",
        "content": "是天旋地转的感觉，还是头重脚轻？",
        "technique": "clarification",
        "purpose": "differentiate_vertigo",
        "reasoning": "眩晕多为前庭/脑血管问题，头晕多为心血管问题"
      }
    ],
    "key_techniques_demonstrated": [
      "clarification",
      "red_flag_check",
      "risk_factor_assessment"
    ]
  },

  // === 物理检查要求 (NEW) ===
  "physical_examination_requirements": {
    "mandatory_checks": [
      {
        "check_type": "blood_pressure",
        "importance": "critical",
        "interpretation": {
          "if_high": ">140/90，考虑高血压",
          "if_low": "<90/60，考虑低血压"
        }
      }
    ]
  },

  // === 深度患者画像 (NEW) ===
  "patient_profile": {
    "demographics": {
      "age": 45,
      "occupation": "出租车司机"
    },
    "emotional_state": {
      "sources": [
        {
          "type": "fear_of_serious_illness",
          "trigger": "邻居脑出血",
          "patient_statements": ["我是不是得了脑瘤？"]
        },
        {
          "type": "occupational_concern",
          "statement_example": "我要开车，头晕不能开车啊"
        }
      ]
    },
    "social_context": {
      "family_support": "limited"
    },
    "health_literacy": {
      "misconceptions": ["认为头晕就是脑供血不足"],
      "information_sources": ["网络搜索", "抖音"]
    }
  },

  // === 严谨的矛盾设计 (IMPROVED) ===
  "contradiction_scenarios": [
    {
      "design_purpose": "测试Agent是否主动询问用药",
      "agent_evaluation_criteria": {
        "must_do": [...],
        "must_not_do": [...],
        "scoring": {...}
      }
    }
  ],

  // === v1 保留字段 ===
  "patient_behavior": {...},
  "system_records": {...},
  "red_line_tests": {...}
}
```

---

## 🎯 关键改进点详解

### 1. 从"该问什么"到"如何追问"

**v1**:
```json
"question": "这个问题持续多久了？"
```

**v2**:
```json
{
  "question": "头晕多久了？",
  "follow_up_based_on_answer": {
    "if_short_term": "<3天，询问诱因",
    "if_long_term": ">3个月，询问模式"
  },
  "reasoning": "急慢性头晕鉴别诊断完全不同"
}
```

### 2. 从"简单标注"到"深度画像"

**v1**:
```json
"emotional_state": {"type": "anxious"}
```

**v2**:
```json
{
  "sources": [
    {
      "type": "fear_of_serious_illness",
      "trigger": "邻居脑出血",
      "patient_statements": ["我是不是得了脑瘤？"]
    },
    {
      "type": "financial_concern",
      "statement_example": "如果不需要做太贵的检查就好了"
    },
    {
      "type": "occupational_concern",
      "statement_example": "我要开车，头晕不能开车啊"
    }
  ]
}
```

### 3. 从"矛盾标注"到"训练目的"

**v1**:
```json
"withholding": ["current_medications"]
```

**v2**:
```json
{
  "design_purpose": "测试Agent是否主动识别用药矛盾",
  "will_reveal_when": "医生明确询问",
  "agent_evaluation_criteria": {
    "must_do": [
      {
        "action": "询问当前用药",
        "failure_consequence": "错过重要信息",
        "points": 1.5
      }
    ]
  }
}
```

---

## 📈 改进效果对比

### 问诊质量

**v1**:
- Agent知道"该问什么"
- 但不知道"如何层层递进"
- 容易变成被动问答

**v2**:
- Agent有明确的鉴别诊断思维
- 知道如何根据回答追问
- 理想对话示例供学习

### 检查完整性

**v1**:
- 没有体格检查要求
- 没有检查报告解读

**v2**:
- 明确的物理检查要求
- 检查结果解读指导
- 更接近真实问诊

### 情感理解

**v1**:
- 简单的情感标签
- 缺乏现实因素

**v2**:
- 多维度情感（心理+经济+社会）
- 具体的患者陈述示例
- 更真实的患者画像

### 评估严谨性

**v1**:
- 矛盾设计简单
- 缺乏评估标准

**v2**:
- 明确的训练目的
- 详细的评估标准
- 清晰的后果说明

---

## 🚀 使用 v2 数据的优势

### 1. 更真实的Agent行为

- 主动追问（鉴别诊断驱动）
- 识别矛盾信息
- 处理复杂情感
- 解读检查报告

### 2. 更全面的评估

- 不仅评估"答对与否"
- 评估"问诊思维"
- 评估"情感处理"
- 评估"矛盾识别"

### 3. 更明确的改进方向

- 理想对话作为参考
- 明确的技巧标注
- 详细的评分标准

---

## 📋 下一步计划

### Phase 1: 补充示例对话 (紧急)

**目标**: 为更多场景添加理想对话

**优先场景**:
- 头痛鉴别诊断
- 用药咨询
- 慢性病管理

### Phase 2: 完善辅助检查 (重要)

**目标**: 添加更多检查场景

**内容**:
- 检查结果解读
- 报告解释对话
- 检查推荐逻辑

### Phase 3: 增加患者画像 (重要)

**目标**: 为所有任务添加深度画像

**内容**:
- 职业影响
- 经济因素
- 家庭背景
- 健康素养

### Phase 4: 测试和验证

**目标**: 使用 v2 数据测试Agent

**验证指标**:
- Agent是否更主动？
- Agent是否识别矛盾？
- Agent是否处理情感？
- 评估是否更准确？

---

## 🏆 总结

tasks_realistic_v2.json 针对**用户指出的4大核心问题**进行了全面改进：

1. ✅ **问诊过程简化** → 鉴别诊断驱动的问诊策略
2. ✅ **物理/辅助检查缺失** → 完整的检查要求和解读
3. ✅ **情感深度不足** → 多维度情感和社会画像
4. ✅ **逻辑设计不严谨** → 明确的训练目的和评估标准

**v2 数据更接近真实临床问诊，能够更全面地测试和训练医疗Agent！** 🎉
