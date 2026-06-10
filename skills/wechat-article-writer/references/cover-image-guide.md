# 封面图生成详细指南

> **重要性**：封面图是文章打开率的关键因素，必须生成一张高质量、吸引眼球的主题封面图。

---

## 一、封面图设计原则

### 1. 鲜明的主题色彩

根据文章类型选择合适的配色方案：

| 文章类型 | 推荐配色 | 色彩代码 | 视觉效果 |
|---------|---------|---------|---------|
| **AI/科技类** | 蓝紫渐变 | #1a1f5c → #7c3aed | 未来感、科技感 |
| **工具/效率类** | 绿橙渐变 | #10b981 → #f97316 | 活力、高效 |
| **数据/分析类** | 蓝绿渐变 | #0891b2 → #06b6d4 | 专业、理性 |
| **创意/设计类** | 粉紫渐变 | #ec4899 → #a855f7 | 创新、灵动 |

### 2. 清晰的视觉层次

**三层结构**：
1. **主标题**：大而醒目（中英文结合更有设计感）
2. **副标题**：简短精炼的中文说明（1句话概括核心价值）
3. **视觉元素**：与主题相关的图标、插画或抽象图形

### 3. 现代化设计风格

当前流行趋势：
- ✅ 3D立体元素（球体、立方体、浮动面板）
- ✅ 玻璃拟态效果（半透明、模糊背景）
- ✅ 渐变光效（发光边缘、光束）
- ✅ 粒子系统（飘浮的点、星星）
- ✅ 简约留白（不拥挤，有呼吸感）

### 4. 情感共鸣

| 目标情绪 | 视觉策略 | 文案方向 |
|---------|---------|----------|
| **好奇** | 神秘光效、未知元素 | "你不知道的秘密" |
| **兴奋** | 爆炸效果、上升箭头 | "改变工作方式" |
| **痛点** | 对比图、前后差异 | "告别重复劳动" |
| **启发** | 灯泡、思考元素 | "新视角" |

---

## 二、封面图提示词模板

### 模板1：AI/大模型类

```
A stunning, eye-catching cover image for [主题名称] article.

Design: vibrant gradient background from deep blue (#1a1f5c) to electric purple (#7c3aed), with glowing particles floating throughout and subtle light effects creating depth.

Central visual elements (positioned behind text):
- 3D floating geometric cubes in glass morphism style, semi-transparent with frosted glass effect
- Each cube contains a glowing icon: code brackets symbol, AI brain circuit pattern, automation gear
- Cubes connected by luminous cyan (#06b6d4) energy lines creating a network visualization
- Soft particle system with small glowing dots scattered across the scene
- Light rays emanating from cubes with lens flare effects

Text layout (CRITICAL - all text centered both horizontally and vertically):
- CENTER of image: Large bold title '[主题名称]' in white, modern sans-serif font with subtle glow
- Directly below title in CENTER: Chinese subtitle '[一句话价值说明]' in elegant font, slightly smaller, 90% opacity

IMPORTANT: All Chinese characters must be clear, readable, and accurate - NO garbled text.
Style: ultra-modern, tech-forward, sci-fi inspired, professional, magazine-quality
Visual mood: innovative, powerful, intelligent, cutting-edge, transformative
```

### 模板2：工具/效率类

```
A professional cover image for [工具名] article.
Design: clean gradient background from green (#10b981) to orange (#f97316) with subtle code-related visual elements.

Background elements: 3D modular blocks or connected nodes representing the tool's architecture, with floating code snippets subtly integrated.

Text layout (CRITICAL - centered composition):
- CENTER: main title "[工具名]" in bold, white font with slight shadow
- Below title: subtitle "[核心价值说明]" in Chinese, elegant font

Visual elements: terminal window frames, abstract code syntax highlighting, geometric shapes connected by lines.
Style: developer-friendly, modern, clean, inspiring, minimal but not boring.
Visual mood: efficient, reliable, professional.
All text in simplified Chinese, clear and minimal.
```

---

## 三、生成执行步骤

### 步骤1：分析主题，确定封面图方向
1. 提取主题关键词（2-3个核心词）
2. 概括核心价值（一句话）
3. 确定目标情绪
4. 选择文章类型

### 步骤2：选择配色方案

```
是AI/智能相关？
├─ 是 → 蓝紫渐变 (#1a1f5c → #7c3aed)
└─ 否 → 继续判断
    ├─ 是开发工具？
    │   └─ 是 → 绿橙渐变 (#10b981 → #f97316)
    └─ 是效率/自动化？
        └─ 是 → 橙粉渐变 (#f97316 → #ec4899)
```

### 步骤3：调用API生成

```bash
cd /Users/zhushengping/Documents/article-gen/.codebuddy/skills/wechat-tech-writer

python scripts/generate_image.py \
  --prompt "你的完整提示词" \
  --api gemini \
  --output cover.png
```

---

## 四、质量检查清单

✅ **文字检查**：
- [ ] 中文文字清晰可读，无乱码
- [ ] 文字数量适中（不超过15个汉字）
- [ ] 文字与背景对比度足够

✅ **颜色检查**：
- [ ] 配色鲜明，吸引眼球
- [ ] 渐变自然，无生硬过渡
- [ ] 整体色调符合主题

✅ **视觉检查**：
- [ ] 视觉重点突出（标题最醒目）
- [ ] 层次清晰
- [ ] 不拥挤，有留白

---

## 五、常见问题排查

### Q1：生成的封面图文字全是英文，没有中文？
**解决**：在提示词多处强调中文，如：
```
All text must be in simplified Chinese (简体中文), clear and readable.
Chinese characters must be clear, readable, and accurate - NO garbled text.
```

### Q2：封面图颜色与预期不符？
**解决**：使用颜色名称替代代码，如 `deep blue to vibrant purple`

### Q3：生成速度很慢或超时？
**解决**：简化提示词，删除次要细节

---

**记住**：封面图是读者对文章的第一印象，值得花时间打磨！
