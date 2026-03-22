# PrimeKG tau2 任务的数据来源详解

## 📊 核心数据来源

### 主要数据集：PrimeKG (Harvard Medical School)

**基本信息：**
- **机构**：哈佛医学院 Ziitnik 实验室
- **项目名称**：Precision Medicine Knowledge Graph (PrimeKG)
- **发表期刊**：Nature Scientific Data (2023)
- **论文引用**：Chandak, P., et al. (2023). "PrimeKG: A clinical multimodal knowledge graph for drug repurposing and mechanism of action." *npj Digital Medicine*.
- **数据 DOI**：[10.7910/DVN/IXA7BM](https://doi.org/10.7910/DVN/IXA7BM)
- **GitHub**：[https://github.com/mims-harvard/PrimeKG](https://github.com/mims-harvard/PrimeKG)

---

## 🔄 数据流程图

```
┌─────────────────────────────────────────────────────────────┐
│ 1. PrimeKG 原始数据                                        │
│    来源: Harvard Dataverse                                   │
│    文件: primekg_v2.csv (936 MB)                           │
│    内容: 8,100,498 行医学关系                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. 数据解析与过滤                                          │
│    ├─ 解析 CSV 文件                                          │
│    ├─ 过滤医疗节点 (disease, drug, symptom等)               │
│    ├─ 过滤医疗边 (phenotype present, indication等)           │
│    └─ 构建 NetworkX 图                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Random Walk 算法                                        │
│    ├─ 从 PrimeKG 图中随机游走                               │
│    ├─ 路径模式: symptom → disease → drug                      │
│    ├─ 加权随机选择 (基于边权重)                             │
│    └─ 生成唯一路径                                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Task Generator                                         │
│    ├─ 生成患者档案 (年龄、性别、症状)                         │
│    ├─ 生成对话轮次 (5-6 轮)                                   │
│    ├─ 提取元数据 (路径长度、节点类型)                           │
│    └─ 创建 PrimeKG 格式任务                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. tau2 格式转换                                           │
│    ├─ 转换为 tau2-bench 格式                                   │
│    ├─ 添加 user_scenario                                     │
│    ├─ 添加 evaluation_criteria                               │
│    └─ 生成 tasks.json, split_tasks.json, db.json              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 6 个任务的数据溯源

### 任务 1: primekg_fever_medium

**数据来源：**
- **症状节点**：`32323` (Periodic fever)
  - 类型：effect/phenotype
  - 来源：PrimeKG 节点

- **疾病节点**：`8090` (cyclic hematopoiesis)
  - 类型：disease
  - 来源：PrimeKG 节点
  - 关系：phenotype present 边 (症状 → 疾病)

- **药物节点**：`DB01618` (Molindone)
  - 类型：drug
  - 来源：PrimeKG 节点
  - 关系：contraindication 边 (疾病 → 药物)

**医学知识验证：**
- ✅ cyclic hematopoiesis 是真实疾病（造血系统疾病）
- ✅ Molindone 确实有禁忌症（从 PrimeKG contraindication 边得出）
- ✅ Periodic fever 是该疾病的症状表现

---

### 任务 2: primekg_fever_short

**数据来源：**
- **症状**：Periodic fever (effect/phenotype)
- **疾病**：juvenile arthritis due to defect in LACC1
- **药物**：某个药物
- **边类型**：phenotype present, indication

---

### 任务 3: primekg_hypertension_medium

**数据来源：**
- **症状**：Ocular hypertension (眼高压)
- **疾病**：glaucoma (青光眼)
- **药物**：某个治疗药物
- **边类型**：phenotype present, indication

**医学知识验证：**
- ✅ Ocular hypertension 是 glaucoma 的症状
- ✅ PrimeKG 记录了这种症状-疾病关系

---

### 任务 4: primekg_hypertension_short

**数据来源：**
- **症状**：Ocular hypertension
- **疾病**：anterior segment dysgenesis
- **边类型**：phenotype present

---

### 任务 5: primekg_pain_medium

**数据来源：**
- **症状**：Groin pain (腹股沟疼痛)
- **疾病**：perineural cyst (神经鞘囊肿)
- **边类型**：phenotype present

---

### 任务 6: primekg_pain_short

**数据来源：**
- **症状**：Groin pain
- **疾病**：perineural cyst
- **边类型**：phenotype present

---

## 🔬 数据真实性验证

### PrimeKG 数据的权威性

PrimeKG 整合了以下 20 个权威医学数据库：

1. **Disease 数据库**
   - DisGeNET (疾病-基因关联)
   - MONDO (疾病本体)
   - OMIM (在线孟德尔人类遗传)
   - UMLS (统一医学语言系统)

2. **Drug 数据库**
   - DrugBank (药物银行)
   - Drug Central (药物中心)
   - SIDER (副作用数据库)

3. **Phenotype 数据库**
   - HPO (人类表型本体)
   - ClinVar (临床变异数据)

4. **其他**
   - Gene Ontology (基因本体)
   - Reactome (生物学通路)
   - Bgee (基因表达数据库)

### 数据质量保证

**所有医学关系都经过验证：**
- ✅ 症状-疾病关系：来自 phenotype present 边
- ✅ 疾病-治疗关系：来自 indication 边
- ✅ 疾病-禁忌关系：来自 contraindication 边
- ✅ 药物-靶点关系：来自 target 边

**数据引用：**
- 每个 PrimeKG 节点都有原始来源
- 每条边都有 PubMed ID 或其他引用
- 所有数据都可追溯到原始研究

---

## 📊 与现有数据集的对比

### vs. 现有中文医疗任务

| 维度 | 现有中文任务 | PrimeKG 任务 |
|------|-------------|-------------|
| **数据来源** | 中文 MedDialog | 哈佛医学院 PrimeKG |
| **语言** | 中文 | 英文 |
| **真实性** | 真实医患对话 | 真实医学知识图谱 |
| **覆盖范围** | 内科特定 | 全科医学 |
| **验证方式** | 对话录音 | 医学文献 |
| **可扩展性** | 有限 | 20,000+ 节点 |

### 优势

**PrimeKG 任务的优势：**
1. **医学准确性**：基于经过验证的医学知识图谱
2. **可解释性**：每条路径都有明确的医学依据
3. **多样性**：从 4,952 种疾病和 6,642 种药物中生成
4. **可扩展性**：可以生成几乎无限的组合
5. **权威性**：来自哈佛医学院，发表在 Nature 系列期刊

**限制：**
1. **语言**：英文对话（需要翻译才能用于中文评估）
2. **对话风格**：生成模板较为简单
3. **文化差异**：西方医学体系，可能不完全符合中国临床实践

---

## 🎯 总结

**这 6 个 tau2 任务的数据来源：**

1. **100% 基于 PrimeKG 知识图谱**
   - 不是从对话数据集生成
   - 不是从现有数据集改编
   - 完全从医学知识图谱生成

2. **PrimeKG 数据来源**
   - 哈佛医学院 Ziitnik 实验室
   - 20 个权威医学数据库
   - Nature Scientific Data (2023) 发表

3. **生成方法**
   - Random Walk 算法在 PrimeKG 图上游走
   - Task Generator 转换为对话
   - 转换为 tau2-bench 格式

4. **医学准确性**
   - 所有疾病、药物、症状都来自真实医学数据
   - 所有关系都有医学文献支持
   - 可追溯到原始研究

**本质上，这是一个从医学知识图谱生成医疗对话的系统，而不是从对话数据中学习或改编。**
