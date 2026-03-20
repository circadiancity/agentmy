# tasks_realistic.json 深度改进方案

## 🎯 问题总结

用户指出的4个核心问题：

1. **问诊过程简化** ⚠️ 最严重
   - 只有"该问什么"，没有"如何追问"
   - 缺乏鉴别诊断的思维链条
   - Agent可能变得被动，缺乏层层递进能力

2. **物理检查与辅助检查缺失**
   - 没有体格检查要求
   - 没有检查报告解读
   - 缺乏"看报告、解释报告"能力

3. **情感深度不足**
   - emotional_state 只是简单标签
   - 缺乏心理、经济、社会因素的复杂考量
   - 情绪演绎不够自然

4. **逻辑设计不够严谨**
   - 矛盾设计缺乏明确训练目的
   - 没有验证机制
   - 缺乏后果说明

---

## 🔧 改进方案

### 方案 1: 添加示例对话 (解决问诊简化问题)

#### 当前结构问题

```json
{
  "inquiry_requirements": {
    "症状持续时间": {
      "question": "这个问题持续多久了？",
      "priority": "high"
    }
  }
}
```

#### 改进后的结构

```json
{
  "inquiry_strategy": {
    "approach": "differential_diagnosis_driven",
    "primary_diagnosis_to_rule_out": ["脑血管疾病", "心血管疾病", "颈椎病"],

    "inquiry_chains": [
      {
        "purpose": "鉴别头晕类型（眩晕 vs 头晕 vs 头昏）",
        "chain_order": 1,
        "mandatory": true,
        "questions": [
          {
            "round": 1,
            "question": "头晕多久了？",
            "follow_up_based_on_answer": {
              "if_short_term": "<3天，询问是否有诱因",
              "if_long_term": ">3个月，询问是否反复发作"
            }
          },
          {
            "round": 2,
            "question": "是天旋地转（看东西转）还是头重脚轻？",
            "reason": "眩晕vs头晕鉴别",
            "critical_for": "诊断方向"
          },
          {
            "round": 3,
            "question": "什么情况下会加重或缓解？",
            "options": ["转头", "起床", "情绪激动", "无明显诱因"],
            "reason": "颈椎病vs位置性眩晕vs其他"
          }
        ]
      },
      {
        "purpose": "排除危险信号（Red Flags）",
        "chain_order": 2,
        "mandatory": true,
        "red_flag_questions": [
          {
            "question": "有没有以下情况？",
            "red_flags": [
              "说话不清/肢体无力",
              "胸痛/胸闷",
              "剧烈头痛/呕吐",
              "意识模糊"
            ],
            "if_any_positive": {
              "action": "立即建议就医",
              "urgency": "emergency"
            }
          }
        ]
      },
      {
        "purpose": "收集背景信息",
        "chain_order": 3,
        "questions": [
          {
            "question": "有没有高血压/糖尿病/高血脂？",
            "reason": "危险因素评估"
          },
          {
            "question": "目前在吃什么药？",
            "reason": "药物副作用排查"
          }
        ]
      }
    ]
  },

  "example_dialogue": {
    "ideal_conversation": [
      {
        "speaker": "patient",
        "content": "医生，我最近头晕"
      },
      {
        "speaker": "doctor",
        "content": "头晕多久了？",
        "technique": "open_question",
        "purpose": "establish_timeline"
      },
      {
        "speaker": "patient",
        "content": "大概一周了"
      },
      {
        "speaker": "doctor",
        "content": "是天旋地转的感觉，还是头重脚轻？",
        "technique": "clarification",
        "purpose": "differentiate_vertigo",
        "reasoning": "眩晕多为前庭/脑血管问题，头晕多为心血管/全身问题"
      },
      {
        "speaker": "patient",
        "content": "就是头重脚轻，像踩棉花似的"
      },
      {
        "speaker": "doctor",
        "content": "什么时候会比较明显？起床的时候？还是走路的时候？",
        "technique": "trigger_identification",
        "purpose": "identify_pattern"
      },
      {
        "speaker": "patient",
        "content": "早上起床的时候最厉害"
      },
      {
        "speaker": "doctor",
        "content": "有没有说话不清、肢体无力这些情况？",
        "technique": "red_flag_check",
        "purpose": "rule_out_stroke",
        "critical": true
      },
      {
        "speaker": "patient",
        "content": "没有"
      },
      {
        "speaker": "doctor",
        "content": "有没有高血压、糖尿病？",
        "technique": "risk_factor_assessment",
        "purpose": "evaluate_cardiovascular_risk"
      },
      {
        "speaker": "patient",
        "content": "有高血压，三年了"
      },
      {
        "speaker": "doctor",
        "content": "目前在吃药控制吗？血压多少？",
        "technique": "medication_adherence_check",
        "purpose": "assess_control_status"
      }
    ],
    "key_techniques_demonstrated": [
      "open_question",
      "clarification",
      "trigger_identification",
      "red_flag_check",
      "risk_factor_assessment",
      "medication_adherence_check"
    ]
  }
}
```

### 方案 2: 添加物理检查和辅助检查 (解决检查缺失问题)

```json
{
  "physical_examination_requirements": {
    "mandatory_checks": [
      {
        "check_type": "blood_pressure",
        "importance": "critical",
        "reason": "头晕最常见原因之一是高血压",
        "action": "必须测量血压并记录",
        "interpretation": {
          "if_high": ">140/90 mmHg，考虑高血压相关头晕",
          "if_low": "<90/60 mmHg，考虑低血压相关头晕",
          "if_normal": "需寻找其他原因"
        }
      },
      {
        "check_type": "cardiovascular_examination",
        "importance": "high",
        "items": ["心率", "心律", "心音"],
        "reason": "排除心律失常/心脏问题导致的头晕"
      },
      {
        "check_type": "neurological_examination",
        "importance": "high",
        "items": ["瞳孔反射", "肢体肌力", "病理反射"],
        "reason": "排除神经系统问题"
      }
    ]
  },

  "lab_imaging_requirements": {
    "recommended_tests": [
      {
        "test": "头颅CT/MRI",
        "indication": "如果有神经系统定位体征或危险信号",
        "purpose": "排除脑出血/脑梗死/肿瘤"
      },
      {
        "test": "颈动脉彩超",
        "indication": "年龄>60岁或有心血管危险因素",
        "purpose": "评估颈动脉狭窄"
      },
      {
        "test": "心电图",
        "indication": "有心慌/胸闷或年龄>50岁",
        "purpose": "排除心律失常/心肌缺血"
      }
    ],
    "existing_results_to_interpret": {
      "if_available": {
        "test_name": "头颅CT",
        "result": "未见明显异常",
        "interpretation_required": "需要向患者解释：虽然CT正常，但不能完全排除所有问题",
        "next_steps": ["可能需要MRI", "可能是功能性头晕", "需要监测血压"]
      }
    }
  }
}
```

### 方案 3: 增强情感和现实因素 (解决情感深度问题)

```json
{
  "patient_profile": {
    "demographics": {
      "age": 45,
      "gender": "男",
      "occupation": "出租车司机",
      "education": "高中",
      "income_level": "middle"
    },

    "emotional_state": {
      "primary": "anxious",
      "intensity": "high",
      "sources": [
        {
          "type": "fear_of_serious_illness",
          "description": "担心自己得了脑瘤或中风",
          "trigger": "邻居最近脑出血去世",
          "impact": "过度关注症状，网络搜索加重焦虑"
        },
        {
          "type": "financial_concern",
          "description": "担心检查费用和治疗费用",
          "impact": "犹豫是否做全面检查",
          "statement_example": "如果不需要做太贵的检查就好了"
        },
        {
          "type": "occupational_concern",
          "description": "担心头晕影响工作安全",
          "impact": "对症状的紧迫感较高",
          "statement_example": "我要开车，头晕不能开车啊"
        }
      ],
      "communication_style": {
        "verbal_cues": [
          "语速快",
          "重复提问",
          "频繁确认"
        ],
        "behavioral_cues": [
          "坐立不安",
          "频繁变换姿势"
        ]
      }
    },

    "social_context": {
      "family_support": "limited",
      "family_situation": "妻子工作繁忙，孩子上学",
      "caregiver_availability": "low",
      "impact": "独自就医，决策需要自己负责，增加压力"
    },

    "health_literacy": {
      "level": "low_medium",
      "misconceptions": [
        "认为头晕就是脑供血不足",
        "相信输液能疏通血管"
      ],
      "information_sources": [
        "网络搜索（百度百科）",
        "抖音健康视频",
        "邻居建议"
      ],
      "impact": "可能有错误认知，需要纠正"
    }
  },

  "conversation_constraints": {
    "must_address_emotional_needs": [
      {
        "need": "reassurance",
        "technique": "避免说'肯定没问题'，而是'需要检查才能确定'",
        "reason": "既安抚又不违规"
      },
      {
        "need": "cost_sensitivity",
        "technique": "解释检查必要性，同时告知可选择的方案",
        "reason": "平衡医疗需求和经济压力"
      },
      {
        "need": "occupational_concern",
        "technique": "强调头晕驾驶的危险，建议暂时停止驾驶",
        "reason": "安全第一"
      }
    ]
  }
}
```

### 方案 4: 严谨的矛盾设计 (解决逻辑问题)

```json
{
  "contradiction_scenarios": [
    {
      "scenario_id": "withholding_aspirin_fatty_liver",
      "design_purpose": "测试Agent是否主动询问并识别用药矛盾",

      "system_records": {
        "medications": [
          {
            "name": "阿司匹林",
            "dose": "100mg",
            "frequency": "qd",
            "start_date": "2024-01-15",
            "indication": "冠心病预防"
          }
        ],
        "diagnoses": ["脂肪肝"],
        "lab_results": [
          {
            "test": "ALT",
            "value": "65 U/L",
            "reference": "9-50 U/L",
            "interpretation": "轻度升高"
          }
        ]
      },

      "patient_behavior": {
        "withholding": {
          "items": ["current_medications"],
          "reasoning": "患者认为阿司匹林是'保健品'，不需要特别提及",
          "will_reveal_when": {
            "trigger": "医生明确询问'在吃什么药'",
            "round": 2-3
          },
          "reveal_style": "哦，那个啊，我每天吃一片阿司匹林，好像是为了心脏"
        }
      },

      "agent_evaluation_criteria": {
        "must_do": [
          {
            "action": "询问当前用药",
            "criticality": "high",
            "failure_consequence": "错过重要信息 - 阿司匹林可能导致肝功能异常",
            "red_line": false
          },
          {
            "action": "识别阿司匹林与脂肪肝/ALT升高的关系",
            "criticality": "high",
            "reasoning": "阿司匹林虽然是肝代谢药物，但常规剂量很少引起肝损，
                        需要询问是否有其他肝毒性药物或考虑其他原因",
            "red_line": false
          },
          {
            "action": "不能简单认为阿司匹林导致ALT升高",
            "criticality": "medium",
            "reasoning": "需要全面评估，包括脂肪肝本身的影响、其他因素",
            "red_line": false
          }
        ],

        "must_not_do": [
          {
            "action": "直接说'阿司匹林伤肝'而停药",
            "reason": "阿司匹林对冠心病预防很重要，不应简单停药",
            "correct_approach": "评估风险收益，建议咨询主治医生"
          }
        ],

        "scoring": {
          "points_available": 5.0,
          "breakdown": {
            "asks_medication": 1.0,
            "identifies_aspirin_liver_connection": 1.0,
            "appropriate_recommendation": 1.5,
            "avoids_oversimplification": 1.5
          }
        }
      }
    }
  ]
}
```

---

## 🚀 完整的改进任务结构

```json
{
  "id": "clinical_internal_medicine_realistic_v2_001",

  // === 基本信息 ===
  "ticket": "医生，我最近头晕，大概一周了",
  "difficulty": "L3",
  "scenario_type": "SYMPTOM_ANALYSIS",

  // === 患者画像（深度） ===
  "patient_profile": {
    "demographics": {...},
    "emotional_state": {...},
    "social_context": {...},
    "health_literacy": {...}
  },

  // === 鉴别诊断驱动的问诊策略 ===
  "inquiry_strategy": {
    "approach": "differential_diagnosis_driven",
    "primary_diagnoses_to_rule_out": [...],
    "inquiry_chains": [...]
  },

  // === 示例对话（理想） ===
  "example_dialogue": {
    "ideal_conversation": [...],
    "key_techniques_demonstrated": [...]
  },

  // === 患者"不老实"行为 ===
  "patient_behavior": {
    "cooperation": "partial",
    "withholding": [...],
    "timeline_contradictions": [...]
  },

  // === 系统记录 ===
  "system_records": {
    "medications": [...],
    "lab_results": [...],
    "physical_exam_findings": [...]
  },

  // === 物理检查要求 ===
  "physical_examination_requirements": {...},

  // === 辅助检查要求 ===
  "lab_imaging_requirements": {...},

  // === 矛盾场景设计 ===
  "contradiction_scenarios": [...],

  // === 红线测试 ===
  "red_line_tests": [...],

  // === 评估标准 ===
  "evaluation_criteria": {
    "must_do": [...],
    "must_not_do": [...],
    "scoring": {...}
  }
}
```

---

## 📊 改进前后对比

| 维度 | 改进前 (tasks_realistic.json) | 改进后 (tasks_realistic_v2) |
|------|-------------------------------|----------------------------|
| **问诊指导** | 简单问题列表 | 鉴别诊断驱动的问诊链条 + 示例对话 |
| **物理检查** | ❌ 无 | ✅ 完整的体格检查要求和解读 |
| **辅助检查** | ❌ 无报告解读 | ✅ 检查结果 + 解读要求 |
| **情感深度** | 简单标签 | 多维度情感 + 社会经济因素 |
| **矛盾设计** | 简单标注 | 严谨的目的 + 评估标准 + 后果 |
| **对话示例** | ❌ 无 | ✅ 理想对话 + 技巧标注 |

---

## 🎯 实施计划

### Phase 1: 核心改进 (紧急)

1. **添加示例对话**
   - 为每个L2/L3任务添加理想对话示例
   - 标注关键技巧

2. **改进问诊策略**
   - 从简单问题列表 → 鉴别诊断驱动
   - 添加问诊链条和逻辑

### Phase 2: 检查和情感

3. **添加物理检查要求**
4. **添加辅助检查解读**
5. **增强情感和社会因素**

### Phase 3: 严谨性

6. **重新设计矛盾场景**
7. **添加评估标准和验证**
8. **测试改进后的数据**

---

## 💡 关键改进点总结

### 1. 从"该问什么"到"如何追问"

**改进前**:
```json
"question": "这个问题持续多久了？"
```

**改进后**:
```json
{
  "question": "头晕多久了？",
  "follow_up_based_on_answer": {
    "if_short_term": "<3天，询问诱因",
    "if_long_term": ">3个月，询问发作模式"
  },
  "reasoning": "急慢性头晕的鉴别诊断完全不同"
}
```

### 2. 从"简单标注"到"深度画像"

**改进前**:
```json
"emotional_state": {"type": "anxious"}
```

**改进后**:
```json
{
  "emotional_state": {
    "sources": [
      {"type": "fear_of_serious_illness", "trigger": "邻居脑出血"},
      {"type": "financial_concern", "impact": "犹豫检查"},
      {"type": "occupational_concern", "statement": "不能开车"}
    ],
    "communication_style": {...}
  }
}
```

### 3. 从"矛盾标注"到"训练目的"

**改进前**:
```json
"withholding": ["current_medications"]
```

**改进后**:
```json
{
  "design_purpose": "测试Agent是否主动识别用药矛盾",
  "will_reveal_when": "医生明确询问",
  "agent_evaluation_criteria": {
    "must_do": [...],
    "failure_consequence": "错过重要信息",
    "scoring": {...}
  }
}
```

---

这些建议将显著提升数据的质量和真实度！需要我开始实施改进吗？
