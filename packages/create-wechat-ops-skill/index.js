#!/usr/bin/env node
/**
 * create-wechat-ops-skill
 *
 * 一键安装「公众号运营复盘」Claude Code 技能。
 * 从 GitHub 仓库 DwDestiny/my_skill 的子目录拉取只读模板，投放到
 * ~/.claude/skills/wechat-ops-performance-review，供 Claude Code 自动发现。
 *
 * 设计契约（与技能 #16 对齐）:
 *   - 技能目录只读:本脚本只投放模板 + 打印下一步,绝不在技能目录里写运行态数据。
 *   - 运行态数据写工作区 ~/.wxops,由技能自身的 `wxops init` 创建。
 */

import os from "node:os";
import path from "node:path";
import process from "node:process";
import fs from "node:fs";
import readline from "node:readline";
import { downloadTemplate } from "giget";

const REPO = "DwDestiny/my_skill";
const SUBDIR = "skills/wechat-ops-performance-review";
const DEFAULT_REF = "main";
const SKILL_DIRNAME = "wechat-ops-performance-review";

function printHelp() {
  const lines = [
    "",
    "create-wechat-ops-skill — 一键安装「公众号运营复盘」Claude Code 技能",
    "",
    "用法:",
    "  npx create-wechat-ops-skill [目标目录] [选项]",
    "",
    "参数:",
    "  目标目录            技能安装位置(可选)。默认:",
    "                     ~/.claude/skills/wechat-ops-performance-review",
    "",
    "选项:",
    "  --dir <path>       指定安装目录(等价于位置参数;同时给出时以 --dir 为准)",
    "  --ref <ref>        拉取的 Git 分支/标签/commit(默认: main)",
    "  --force            目标目录已存在时允许写入(合并:覆盖同名文件,保留其它内容)",
    "  --force-clean      先递归清空目标目录再写入(破坏性,需交互确认)",
    "  -h, --help         显示本帮助",
    "",
    "示例:",
    "  npx create-wechat-ops-skill",
    "  npx create-wechat-ops-skill ./my-skill --force",
    "  npx create-wechat-ops-skill ./my-skill --force-clean",
    "  npx create-wechat-ops-skill --dir ~/skills/wxops --ref main",
    "",
    "私有仓库:",
    "  若仓库为私有,需先设置环境变量 GIGET_AUTH=<GitHub token>。",
    "",
  ];
  console.log(lines.join("\n"));
}

/**
 * 极简 argv 解析:位置参数(目标目录) + --dir/--ref/--force/--force-clean/--help。
 */
function parseArgs(argv) {
  const opts = {
    dir: null,
    ref: DEFAULT_REF,
    force: false,
    forceClean: false,
    help: false,
    positional: null,
  };

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    switch (arg) {
      case "-h":
      case "--help":
        opts.help = true;
        break;
      case "--force":
        opts.force = true;
        break;
      case "--force-clean":
        opts.forceClean = true;
        break;
      case "--dir":
        opts.dir = argv[++i] ?? null;
        break;
      case "--ref":
        opts.ref = argv[++i] ?? DEFAULT_REF;
        break;
      default:
        if (arg.startsWith("-")) {
          console.error(`未知选项: ${arg}（用 --help 查看用法）`);
          process.exit(1);
        }
        // 第一个位置参数 = 目标目录
        if (opts.positional === null) {
          opts.positional = arg;
        }
        break;
    }
  }

  return opts;
}

function resolveTargetDir(opts) {
  // 优先级: --dir > 位置参数 > 默认 ~/.claude/skills/...
  const raw = opts.dir ?? opts.positional;
  if (raw) {
    // 支持 ~ 前缀展开
    if (raw === "~" || raw.startsWith("~/")) {
      return path.join(os.homedir(), raw.slice(1));
    }
    return path.resolve(raw);
  }
  return path.join(os.homedir(), ".claude", "skills", SKILL_DIRNAME);
}

function printNextSteps(dir) {
  const lines = [
    "",
    "✅ 「公众号运营复盘」技能已安装到:",
    `   ${dir}`,
    "",
    "该目录位于 ~/.claude/skills 下,Claude Code 会自动发现并加载本技能。",
    "技能目录为只读模板;所有运行态数据写入工作区 ~/.wxops,不会污染技能目录。",
    "",
    "下一步:",
    "",
    "① 安装 Python 依赖(playwright + 浏览器内核):",
    `   cd "${dir}"`,
    "   pip install -r requirements.txt",
    "   playwright install chromium",
    "",
    "② 跑通 demo(内置脱敏样本,无需登录、无需 pnpm,验证分析链路):",
    `   python3 "${path.join(dir, "scripts", "wxops")}" analyze --demo --data-only`,
    "",
    "③ 正式使用(抓取真实公众号数据):",
    "   wxops init      # 初始化工作区 ~/.wxops",
    "   wxops login     # 扫码登录公众号后台",
    "   wxops analyze   # 抓取 → 生成报告 → 渲染看板",
    "",
    "提示: `wxops` 即 scripts/wxops,可加入 PATH 或用上面的绝对路径调用。",
    "",
  ];
  console.log(lines.join("\n"));
}

/**
 * 若 --force-clean 为 true,在执行破坏性操作前向用户确认。
 * - 非 TTY 环境(管道/CI):直接拒绝并退出(exit 1)。
 * - TTY 环境:要求用户原样输入 "yes" 才继续,否则取消(exit 0)。
 */
async function confirmForceClean(dir) {
  console.error("");
  console.error("⚠️  警告:--force-clean 将递归删除以下目录的全部内容后再写入:");
  console.error(`   ${dir}`);
  console.error("   此操作不可逆,请确认目录中没有重要文件。");
  console.error("");

  if (!process.stdin.isTTY) {
    console.error("❌ 非交互式环境下拒绝执行 --force-clean(会递归删除目录),请在交互终端手动确认。");
    console.error("");
    process.exit(1);
  }

  // TTY 环境:要求用户原样输入 yes
  const answer = await new Promise((resolve) => {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stderr,
    });
    rl.question('   请输入 "yes" 确认继续,其他任意输入取消: ', (ans) => {
      rl.close();
      resolve(ans.trim());
    });
  });

  if (answer !== "yes") {
    console.error("");
    console.error("已取消。");
    console.error("");
    process.exit(0);
  }

  console.error("");
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));

  if (opts.help) {
    printHelp();
    process.exit(0);
  }

  const dir = resolveTargetDir(opts);
  const source = `gh:${REPO}/${SUBDIR}#${opts.ref}`;

  console.log("");
  console.log("📦 正在拉取「公众号运营复盘」技能模板...");
  console.log(`   来源: ${source}`);
  console.log(`   目标: ${dir}`);
  console.log("");

  // --force-clean 破坏性操作:需通过确认门才能继续
  if (opts.forceClean) {
    await confirmForceClean(dir);
  }

  try {
    await downloadTemplate(source, {
      dir,
      force: opts.force || opts.forceClean,   // 允许写入非空目录
      forceClean: opts.forceClean,             // 仅 --force-clean 触发递归清空
    });

    // 下载结果非空校验: giget 对子目录不存在时静默产出空目录,需在此显式检测
    let entries = [];
    try {
      if (fs.existsSync(dir)) {
        entries = fs.readdirSync(dir);
      }
    } catch {
      entries = [];
    }
    const nonHidden = entries.filter((name) => !name.startsWith("."));
    if (nonHidden.length === 0) {
      throw new Error(
        `未能从来源拉到任何文件: ${source}。常见原因是该子目录在指定 ref 上尚未合并/不存在。`,
      );
    }
  } catch (err) {
    console.error("");
    console.error("❌ 安装失败。");
    const msg = (err && err.message) ? err.message : String(err);
    console.error(`   原因: ${msg}`);
    console.error("");

    // 目标目录已存在的典型提示
    if (/exists|EEXIST|not empty|already/i.test(msg)) {
      console.error("   目标目录可能已存在内容。可选两种覆盖方式:");
      console.error(`     --force      合并写入,保留原有文件:`);
      console.error(`       npx create-wechat-ops-skill "${dir}" --force`);
      console.error(`     --force-clean  先清空再写,会删除目录原有内容(需交互确认):`);
      console.error(`       npx create-wechat-ops-skill "${dir}" --force-clean`);
      console.error("");
    }

    // 统一兜底: 私有仓 / 网络
    console.error("   排查建议:");
    console.error("   - 若仓库为私有,请设置环境变量后重试: GIGET_AUTH=<GitHub token>");
    console.error("   - 检查网络是否能访问 github.com / 代理设置是否正确。");
    console.error(`   - 确认分支/标签存在: --ref ${opts.ref}`);
    console.error("   - 若使用默认分支仍拉到空,可能是技能内容尚未合并进该分支,可尝试用 --ref 指定包含该技能的分支重试。");
    console.error("");
    process.exit(1);
  }

  printNextSteps(dir);
  process.exit(0);
}

main();
