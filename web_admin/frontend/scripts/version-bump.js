#!/usr/bin/env node

/**
 * 自动版本号管理脚本
 * 支持多种版本递增策略
 */

import { readFileSync, writeFileSync } from 'fs';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const packagePath = join(__dirname, '..', 'package.json');

// 获取命令行参数
const bumpType = process.argv[2] || 'patch'; // patch, minor, major, dev

/**
 * 读取当前版本
 */
function getCurrentVersion() {
  const packageJson = JSON.parse(readFileSync(packagePath, 'utf8'));
  return packageJson.version;
}

/**
 * 更新版本号
 */
function updateVersion(currentVersion, type) {
  const [major, minor, patch, ...rest] = currentVersion.split(/[.-]/);
  const isPreRelease = rest.length > 0;

  let newMajor = parseInt(major);
  let newMinor = parseInt(minor);
  let newPatch = parseInt(patch);
  let preRelease = rest.join('-');

  const now = new Date();
  const timestamp = now.toISOString().slice(0, 19).replace(/[-:]/g, '').replace('T', '-');
  const buildNumber = Math.floor(now.getTime() / 1000);

  switch (type) {
    case 'major':
      newMajor++;
      newMinor = 0;
      newPatch = 0;
      preRelease = '';
      break;

    case 'minor':
      newMinor++;
      newPatch = 0;
      preRelease = '';
      break;

    case 'patch':
      if (isPreRelease) {
        // 如果是预发布版本,移除预发布标识
        preRelease = '';
      } else {
        newPatch++;
      }
      break;

    case 'dev':
      preRelease = `dev.${buildNumber}`;
      break;

    case 'build':
      // 构建版本:保持主版本号,添加构建时间戳
      preRelease = `build.${timestamp}`;
      break;

    default:
      throw new Error(`不支持的版本类型: ${type}`);
  }

  let newVersion = `${newMajor}.${newMinor}.${newPatch}`;
  if (preRelease) {
    newVersion += `-${preRelease}`;
  }

  return newVersion;
}

/**
 * 写入新版本到 package.json
 */
function writeNewVersion(newVersion) {
  const packageJson = JSON.parse(readFileSync(packagePath, 'utf8'));
  packageJson.version = newVersion;
  writeFileSync(packagePath, JSON.stringify(packageJson, null, 2) + '\n');
}

/**
 * 获取 Git 信息
 */
function getGitInfo() {
  try {
    const gitHash = execSync('git rev-parse --short HEAD', { encoding: 'utf8' }).trim();
    const gitBranch = execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf8' }).trim();
    const isDirty = execSync('git status --porcelain', { encoding: 'utf8' }).trim() !== '';

    return {
      hash: gitHash,
      branch: gitBranch,
      dirty: isDirty,
    };
  } catch (error) {
    return {
      hash: 'unknown',
      branch: 'unknown',
      dirty: false,
    };
  }
}

/**
 * 主函数
 */
function main() {
  console.log('🚀 开始版本号管理...');

  const currentVersion = getCurrentVersion();
  console.log(`📋 当前版本: ${currentVersion}`);

  const newVersion = updateVersion(currentVersion, bumpType);
  console.log(`📈 新版本: ${newVersion}`);

  writeNewVersion(newVersion);
  console.log(`✅ 版本号已更新到 package.json`);

  const gitInfo = getGitInfo();
  console.log(`📦 构建信息:`);
  console.log(`   版本: ${newVersion}`);
  console.log(`   Git: ${gitInfo.hash} (${gitInfo.branch})`);
  console.log(`   构建时间: ${new Date().toLocaleString('zh-CN')}`);
  console.log(`   状态: ${gitInfo.dirty ? '有未提交更改' : '干净'}`);

  // 输出环境变量格式,供构建工具使用
  console.log(`\n🔧 环境变量:`);
  console.log(`export APP_VERSION="${newVersion}"`);
  console.log(`export GIT_HASH="${gitInfo.hash}"`);
  console.log(`export GIT_BRANCH="${gitInfo.branch}"`);
  console.log(`export BUILD_TIME="${new Date().toISOString()}"`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
