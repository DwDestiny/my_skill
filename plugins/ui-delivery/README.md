# UI Delivery Plugin 配方

**版本：** 0.2.0

这里保存便携 Plugin 的 manifests 和 README。九个 Skill 的维护真源位于源码仓库的 `skills/`；构建时复制到包内 `./skills/`，不会在本目录另存一份。v0.2.0 以 schema v2 创建交付；v1 仅保留 legacy 结构校验。

## 直接使用

只处理某一阶段时，可直接让 Codex 加载对应 Skill；完整交付从 [ui-delivery 总调度](./skills/ui-delivery/SKILL.md) 开始。阶段 Skill 可用用户提供的本阶段真实输入独立工作，不强制补齐所有前置材料。

- [产品规划](./skills/ui-product-planning/SKILL.md)
- [UX 架构](./skills/ui-ux-architecture/SKILL.md)
- [视觉方向](./skills/ui-visual-direction/SKILL.md)
- [设计系统](./skills/ui-design-system/SKILL.md)
- [高保真页面与可点原型](./skills/ui-high-fidelity/SKILL.md)
- [动效设计](./skills/ui-motion-design/SKILL.md)
- [前端实现](./skills/ui-frontend-implementation/SKILL.md)
- [视觉验收](./skills/ui-visual-qa/SKILL.md)

完整交付以用户旅程核对范围，每个范围内页面、screen、state 和关键必需元素都可追溯。若用户要求比较多个图片视觉版本，必须交付实际可查看的图片。运行时先检查现有图像工具；不能生成或查看图片时将该阶段标为阻塞，不能拿文字清单代替。用户指定的模型或服务当前不可用时如实说明，不声称曾使用。

高保真静态基线与可点击原型分开登记，原型可选。最终 QA 需要在真实运行界面逐步点击旅程，并用页面截图或 DOM 证据核对目标页面、状态和关键元素。HTTP 200、成功打开浏览器标签、契约校验和概念图均不单独证明页面已正确渲染或交互通过；每条缺陷的截图应放在对应问题附近。具体字段形状与证据条件以包内 [交接契约](./skills/ui-delivery/references/handoff-contract.md) 为准。

## 构建便携包

在源码仓库根目录构建到一个尚不存在的新目录：

```bash
python3 scripts/build_ui_delivery_plugin.py --output dist/ui-delivery-0.2.0
```

构建器会将维护中的九个 Skill、这份 README、Plugin manifests 和许可证写入一个可移植目录，并生成 ZIP 与 SHA-256 清单。构建不会安装 Plugin，也不会修改全局设置。

在源码仓库中，Skill 维护位置是 `skills/ui-delivery/`；构建命令见仓库根的 `scripts/build_ui_delivery_plugin.py`。解压后的包内入口是 `ui-delivery/skills/ui-delivery/SKILL.md`，其余阶段同在 `ui-delivery/skills/`。包内链接以插件目录为根，不依赖源码仓库的 `docs/`。

## 安装与权限

便携 Plugin 包的安装状态与源码 Skill 的全局软链分开记录。v0.1.0 源码 Skills 曾完成本机全局入口软链安装；这不代表 v0.2.0 便携包已构建或安装。用户可先直接让 Codex 加载包内的 `ui-delivery/skills/<skill-name>/SKILL.md`。如需登记 Plugin，可将解压根放到 Codex 支持的本地 marketplace 根目录，并按目标主机当前 Codex CLI 执行：

```text
codex plugin marketplace add <市场根>
codex plugin add ui-delivery@<市场名>
```

`<市场根>` 下需要同时有解压后的 `ui-delivery/` 目录和 `.agents/plugins/marketplace.json`。文件必须放在 `<市场根>/.agents/plugins/marketplace.json`。以下为 marketplace 配置示例：

```json
{
  "name": "local-ui-skills",
  "interface": { "displayName": "Local UI Skills" },
  "plugins": [
    {
      "name": "ui-delivery",
      "source": { "source": "local", "path": "./ui-delivery" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_INSTALL" },
      "category": "Productivity"
    }
  ]
}
```

解压包后将 `ui-delivery/` 放在 `<市场根>/ui-delivery/`，并把上述 JSON 保存为 `<市场根>/.agents/plugins/marketplace.json`；此时 `./ui-delivery` 才指向正确的本地来源。构建、manifest 校验或 ZIP 哈希均不证明 Plugin 已安装、已加载或界面质量已通过。

## 上游来源

本包只保留原创流程说明与一手来源链接，不复制上游 Skill 正文、第三方软件或 Pro 专有资产。各阶段的来源选择、版本和许可边界记录在 [来源说明](./skills/ui-delivery/references/source-selection.md)。
