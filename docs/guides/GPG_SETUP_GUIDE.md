# GPG Setup Guide for Hardened CI
# GPG 配置指南（硬化 CI）

**Purpose / 目的**: Configure GPG signature verification for protected branches in CI
**Audience / 受众**: Repository administrators with GitHub Settings access
**Estimated Time / 预计时间**: 15 minutes

---

## 📋 Prerequisites / 前置条件

- [ ] GitHub repository admin access
- [ ] GPG key pair generated (or will generate in Step 1)
- [ ] Git configured with GPG signing
- [ ] Access to repository Settings → Secrets and variables → Actions

---

## 🔑 Step 1: Generate GPG Key (If Needed) / 生成 GPG 密钥（如需要）

### Check Existing Keys / 检查现有密钥

```bash
# List existing GPG keys
gpg --list-secret-keys --keyid-format=long

# If you see keys listed, skip to Step 2
# 如果看到密钥列表，跳到步骤 2
```

### Generate New Key / 生成新密钥

```bash
# Generate GPG key
gpg --full-generate-key

# Follow prompts:
# 1. Key type: (1) RSA and RSA (default)
# 2. Key size: 4096
# 3. Expiration: 0 (does not expire) or set expiration date
# 4. Name: Your Name or "Claude Enhancer Bot"
# 5. Email: your-email@example.com or ci-bot@example.com
# 6. Passphrase: (optional, leave empty for CI automation)
```

**Example Output / 示例输出**:
```
gpg: key ABCD1234EFGH5678 marked as ultimately trusted
pub   rsa4096 2024-01-01 [SC]
      ABCD1234EFGH5678IJKL9012MNOP3456QRST7890
uid           Claude Enhancer Bot <ci-bot@example.com>
sub   rsa4096 2024-01-01 [E]
```

**Important / 重要**: Save the full fingerprint:
```
ABCD1234EFGH5678IJKL9012MNOP3456QRST7890
```

---

## 📤 Step 2: Export GPG Public Key / 导出 GPG 公钥

### Get Key ID / 获取密钥 ID

```bash
# List keys with long format
gpg --list-secret-keys --keyid-format=long

# Output example:
# sec   rsa4096/ABCD1234EFGH5678 2024-01-01 [SC]
#       Key fingerprint = ABCD 1234 EFGH 5678 IJKL 9012 MNOP 3456 QRST 7890
#
# The Key ID is: ABCD1234EFGH5678 (16 characters)
```

### Export Public Key / 导出公钥

```bash
# Replace KEY_ID with your actual key ID
export KEY_ID="ABCD1234EFGH5678"

# Export public key to file
gpg --armor --export $KEY_ID > gpg_public_key.asc

# Display the public key (for copying)
cat gpg_public_key.asc
```

**Expected Format / 预期格式**:
```
-----BEGIN PGP PUBLIC KEY BLOCK-----

mQINBGXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
... (many lines of base64 encoded data)
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX=
-----END PGP PUBLIC KEY BLOCK-----
```

---

## 🔐 Step 3: Configure GitHub Secrets / 配置 GitHub Secrets

### Navigate to Repository Settings / 进入仓库设置

1. Go to your GitHub repository
2. Click **Settings** (repository settings, not profile)
3. Navigate to **Secrets and variables** → **Actions**
4. Click **New repository secret**

### Secret 1: GPG_PUBLIC_KEY

**Name / 名称**: `GPG_PUBLIC_KEY`

**Value / 值**: Paste the entire content of `gpg_public_key.asc`
```
-----BEGIN PGP PUBLIC KEY BLOCK-----

mQINBGXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
... (all lines)
-----END PGP PUBLIC KEY BLOCK-----
```

**Important / 重要**: Include the `BEGIN` and `END` lines!

### Update Workflow: GPG_FINGERPRINT

**File / 文件**: `.github/workflows/hardened-gates.yml`

**Line to Update / 需更新的行**:
```yaml
env:
  # ... other variables ...

  # GPG fingerprint for verification (update with actual fingerprint)
  GPG_FINGERPRINT: "ABCD1234EFGH5678IJKL9012MNOP3456QRST7890"
```

**Replace with / 替换为**: Your 40-character fingerprint (no spaces)

---

## ✍️ Step 4: Configure Git for Signed Commits / 配置 Git 签名提交

### Local Git Configuration / 本地 Git 配置

```bash
# Set GPG key for signing
git config --global user.signingkey $KEY_ID

# Enable automatic commit signing
git config --global commit.gpgsign true

# Enable automatic tag signing
git config --global tag.gpgsign true

# Verify configuration
git config --global --get user.signingkey
git config --global --get commit.gpgsign
```

### Test Signed Commit / 测试签名提交

```bash
# Create a test commit
echo "test" > test.txt
git add test.txt
git commit -m "test: GPG signing verification"

# Verify signature
git verify-commit HEAD

# Expected output:
# gpg: Signature made ...
# gpg: Good signature from "Claude Enhancer Bot <ci-bot@example.com>"
```

### Add GPG Key to GitHub Profile / 添加 GPG 密钥到 GitHub 个人资料

1. Go to **GitHub Profile Settings** (not repository settings)
2. Navigate to **SSH and GPG keys**
3. Click **New GPG key**
4. Paste the content of `gpg_public_key.asc`
5. Click **Add GPG key**

**Result / 结果**: Your commits will show "Verified" badge on GitHub

---

## 🧪 Step 5: Test CI Workflow / 测试 CI 工作流

### Create a Test PR / 创建测试 PR

```bash
# Create test branch
git checkout -b test/gpg-verification

# Make a signed commit
echo "GPG test" >> README.md
git add README.md
git commit -S -m "test: verify GPG in CI"

# Push to remote
git push origin test/gpg-verification

# Create PR via GitHub UI or gh CLI
gh pr create --title "Test: GPG Verification" --body "Testing hardened-gates.yml GPG verification"
```

### Verify CI Workflow / 验证 CI 工作流

1. Go to PR page
2. Check **Checks** tab
3. Look for **Hardened Quality Gates (GPG + Artifacts)** workflow
4. Expand **🔐 GPG Signature Verification** job
5. Verify output:
   ```
   ✅ Commit abc123 verified with correct GPG key
   ✅ All commits properly signed with authorized GPG key
   ```

### Expected Failures (Without Configuration) / 预期失败（未配置时）

**Without GPG_PUBLIC_KEY secret**:
```
❌ GPG public key not found in secrets
```

**With wrong fingerprint in workflow**:
```
⚠️  Commit abc123 signed with unexpected key: XXXX...
   Expected: ABCD1234EFGH5678IJKL9012MNOP3456QRST7890
❌ GPG VERIFICATION FAILED
```

**Unsigned commit**:
```
❌ Commit abc123 is NOT signed or signature invalid
❌ GPG VERIFICATION FAILED
```

---

## 🔧 Step 6: Troubleshooting / 故障排除

### Issue 1: "gpg: signing failed: No secret key"
### 问题 1："gpg: 签名失败：无秘密密钥"

**Solution / 解决方案**:
```bash
# Check if key exists
gpg --list-secret-keys --keyid-format=long

# If no keys, generate one (Step 1)
# If key exists, verify it's set in git config
git config --global user.signingkey
```

---

### Issue 2: "gpg: signing failed: Inappropriate ioctl for device"
### 问题 2："gpg: 签名失败：设备不适当的 ioctl"

**Solution / 解决方案**:
```bash
# Add to ~/.bashrc or ~/.zshrc
export GPG_TTY=$(tty)

# Or set in Git config
git config --global gpg.program gpg
```

---

### Issue 3: CI can't import GPG key / CI 无法导入 GPG 密钥

**Solution / 解决方案**:
1. Verify secret name is exactly `GPG_PUBLIC_KEY` (case-sensitive)
2. Ensure key includes BEGIN/END lines
3. Check for extra spaces or newlines
4. Re-export and paste again

---

### Issue 4: Fingerprint mismatch in CI / CI 中指纹不匹配

**Solution / 解决方案**:
```bash
# Get your actual fingerprint (40 chars, no spaces)
gpg --list-keys --keyid-format=long --with-colons | grep '^fpr' | head -1 | cut -d: -f10

# Update in .github/workflows/hardened-gates.yml
GPG_FINGERPRINT: "YOUR_40_CHARACTER_FINGERPRINT"
```

---

### Issue 5: "No commits to verify" / "无提交需验证"

**Cause / 原因**: Workflow only runs on main/master/production pushes or PRs

**Solution / 解决方案**: Push to a protected branch or create a PR targeting main

---

## 📊 Verification Checklist / 验证清单

- [ ] GPG key generated
- [ ] Public key exported to `gpg_public_key.asc`
- [ ] `GPG_PUBLIC_KEY` secret added to GitHub
- [ ] `GPG_FINGERPRINT` updated in `hardened-gates.yml`
- [ ] Git configured for automatic signing
- [ ] GPG key added to GitHub profile (for Verified badge)
- [ ] Test commit signed and verified locally
- [ ] Test PR created with signed commit
- [ ] CI workflow ran and verified GPG signature
- [ ] Unsigned commit test (should fail)

---

## 🎯 Success Criteria / 成功标准

### Passing CI Workflow / CI 工作流通过

```
✅ GPG Signature Verification
   - Imported GPG public key
   - Verified 3 commits
   - All signatures valid
   - Fingerprints match

✅ Quality Gate Check
   - Score: 90 >= 85
   - Coverage: 85% >= 80%
   - Signatures: 8/8

✅ Hook Integrity
   - All hooks present
   - All hooks executable
   - Shellcheck passed
```

### Failing CI Workflow (Expected) / CI 工作流失败（预期）

```
❌ GPG Signature Verification
   - Commit abc123 is NOT signed

Action Required:
1. Sign the commit: git commit --amend -S --no-edit
2. Force push: git push -f
```

---

## 🔗 Additional Resources / 额外资源

### Official Documentation / 官方文档
- [GitHub: Signing Commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits)
- [GitHub: Adding GPG Key](https://docs.github.com/en/authentication/managing-commit-signature-verification/adding-a-gpg-key-to-your-github-account)
- [GPG Manual](https://www.gnupg.org/documentation/manuals/gnupg/)

### Internal Documentation / 内部文档
- Hardened Gates Workflow: `.github/workflows/hardened-gates.yml`
- Hardening Status: `HARDENING_STATUS.md`
- Chimney Test Report: `evidence/CHIMNEY_TEST_REPORT.md`

---

## 📝 Notes / 注意事项

### Security Best Practices / 安全最佳实践

1. **Passphrase Protection / 密码保护**: For personal keys, use a strong passphrase
2. **Key Expiration / 密钥过期**: Set expiration date for production keys
3. **Backup / 备份**: Export and securely store private key backup
4. **Rotation / 轮换**: Rotate keys annually or when compromised
5. **Revocation Certificate / 吊销证书**: Generate and store securely

### CI/CD Considerations / CI/CD 考虑事项

1. **Bot Account / 机器人账户**: Use dedicated GitHub bot account for CI commits
2. **Separate Keys / 独立密钥**: Use different keys for dev and CI
3. **No Passphrase for CI / CI 不使用密码**: CI keys should have empty passphrase
4. **Restrict Access / 限制访问**: Only trusted maintainers can push to protected branches

---

## ✅ Completion / 完成

Once all steps are completed and verified:

```
╔═══════════════════════════════════════════════════╗
║  🔐 GPG Verification Configured                  ║
║  ✅ Secrets added to GitHub                      ║
║  ✅ Workflow updated with fingerprint            ║
║  ✅ Local Git configured for signing             ║
║  ✅ CI workflow tested and passing               ║
║  🚀 Ready for production use                     ║
╚═══════════════════════════════════════════════════╝
```

**Next Step / 下一步**: Merge hardening changes to main branch via PR

---

**Document Version / 文档版本**: 1.0
**Last Updated / 最后更新**: 2025-10-13
**Maintained By / 维护者**: Claude Enhancer Team
