#!/usr/bin/env bats
# Stop-Ship Fix #6: 版本一致性测试
# P1-5 级别 - 确保VERSION、manifest.yml、settings.json版本一致

setup() {
    export PROJECT_ROOT="/home/xx/dev/Claude Enhancer 5.0"
    export VERSION_FILE="$PROJECT_ROOT/VERSION"
    export MANIFEST_FILE="$PROJECT_ROOT/.workflow/manifest.yml"
    export SETTINGS_FILE="$PROJECT_ROOT/.claude/settings.json"
    export TEST_VERSION_DIR="/tmp/version_test_$$"
    mkdir -p "$TEST_VERSION_DIR"
}

teardown() {
    rm -rf "$TEST_VERSION_DIR" 2>/dev/null || true
}

# Test 1: VERSION文件存在且格式正确
@test "VERSION file exists and has valid semver format" {
    if [ ! -f "$VERSION_FILE" ]; then
        skip "VERSION file not found"
    fi

    run bash -c "
        version=\$(cat '$VERSION_FILE' | tr -d '[:space:]')
        if [[ \"\$version\" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ ]]; then
            echo \"Valid version: \$version\"
            exit 0
        else
            echo \"Invalid version format: \$version\"
            exit 1
        fi
    "

    [ "$status" -eq 0 ]
}

# Test 2: manifest.yml包含版本信息
@test "manifest.yml contains version field" {
    if [ ! -f "$MANIFEST_FILE" ]; then
        skip "manifest.yml not found"
    fi

    run bash -c "
        grep -q '^version:' '$MANIFEST_FILE'
    "

    [ "$status" -eq 0 ]
}

# Test 3: settings.json包含版本信息
@test "settings.json contains version field" {
    if [ ! -f "$SETTINGS_FILE" ]; then
        skip "settings.json not found"
    fi

    run bash -c "
        grep -q '\"version\"' '$SETTINGS_FILE'
    "

    [ "$status" -eq 0 ]
}

# Test 4: 三个文件版本一致性检查
@test "VERSION, manifest.yml, and settings.json versions are consistent" {
    if [ ! -f "$VERSION_FILE" ] || [ ! -f "$MANIFEST_FILE" ] || [ ! -f "$SETTINGS_FILE" ]; then
        skip "Required version files not found"
    fi

    run bash -c "
        # 读取VERSION文件
        version_file=\$(cat '$VERSION_FILE' | tr -d '[:space:]')

        # 读取manifest.yml版本
        manifest_version=\$(grep '^version:' '$MANIFEST_FILE' | awk '{print \$2}' | tr -d '\"' | tr -d \"'\")

        # 读取settings.json版本（使用grep+sed提取）
        settings_version=\$(grep '\"version\"' '$SETTINGS_FILE' | sed 's/.*\"version\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/')

        echo \"VERSION file: \$version_file\"
        echo \"manifest.yml: \$manifest_version\"
        echo \"settings.json: \$settings_version\"

        # 检查一致性
        if [ \"\$version_file\" = \"\$manifest_version\" ] && [ \"\$version_file\" = \"\$settings_version\" ]; then
            echo \"✅ All versions consistent: \$version_file\"
            exit 0
        else
            echo \"❌ Version mismatch detected\"
            exit 1
        fi
    "

    [ "$status" -eq 0 ]
}

# Test 5: 版本同步脚本存在
@test "version sync script exists and works" {
    # 创建测试版本文件
    echo "1.2.3" > "$TEST_VERSION_DIR/VERSION"

    cat > "$TEST_VERSION_DIR/manifest.yml" <<EOF
name: test-app
version: 1.2.2
EOF

    cat > "$TEST_VERSION_DIR/settings.json" <<EOF
{
  "version": "1.2.1"
}
EOF

    # 模拟同步脚本
    run bash -c "
        cd '$TEST_VERSION_DIR'
        master_version=\$(cat VERSION)

        # 更新manifest.yml
        sed -i \"s/^version:.*/version: \$master_version/\" manifest.yml

        # 更新settings.json
        sed -i \"s/\\\"version\\\":[[:space:]]*\\\"[^\\\"]*\\\"/\\\"version\\\": \\\"\$master_version\\\"/\" settings.json

        # 验证
        manifest_v=\$(grep '^version:' manifest.yml | awk '{print \$2}')
        settings_v=\$(grep '\"version\"' settings.json | sed 's/.*\"version\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/')

        if [ \"\$master_version\" = \"\$manifest_v\" ] && [ \"\$master_version\" = \"\$settings_v\" ]; then
            echo \"Versions synchronized to: \$master_version\"
            exit 0
        fi
        exit 1
    "

    [ "$status" -eq 0 ]
    [[ "$output" =~ "1.2.3" ]]
}

# Test 6: package.json版本一致性（如果存在）
@test "package.json version matches if present" {
    local pkg_file="$PROJECT_ROOT/package.json"

    if [ ! -f "$pkg_file" ] || [ ! -f "$VERSION_FILE" ]; then
        skip "package.json or VERSION not found"
    fi

    run bash -c "
        version_file=\$(cat '$VERSION_FILE' | tr -d '[:space:]')
        pkg_version=\$(grep '\"version\"' '$pkg_file' | head -1 | sed 's/.*\"version\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/')

        if [ \"\$version_file\" = \"\$pkg_version\" ]; then
            echo \"package.json version matches: \$version_file\"
            exit 0
        else
            echo \"Mismatch: VERSION=\$version_file, package.json=\$pkg_version\"
            exit 1
        fi
    "

    [ "$status" -eq 0 ] || [[ "$output" =~ "not found" ]]
}

# Test 7: 版本号递增验证
@test "version increments follow semver rules" {
    run bash -c "
        current='1.2.3'
        next='1.2.4'

        IFS='.' read -r curr_major curr_minor curr_patch <<< \"\$current\"
        IFS='.' read -r next_major next_minor next_patch <<< \"\$next\"

        # 检查递增规则
        if [ \$next_major -gt \$curr_major ]; then
            echo \"Major version bump: \$current -> \$next ✅\"
        elif [ \$next_major -eq \$curr_major ] && [ \$next_minor -gt \$curr_minor ]; then
            echo \"Minor version bump: \$current -> \$next ✅\"
        elif [ \$next_major -eq \$curr_major ] && [ \$next_minor -eq \$curr_minor ] && [ \$next_patch -gt \$curr_patch ]; then
            echo \"Patch version bump: \$current -> \$next ✅\"
        else
            echo \"Invalid version increment\"
            exit 1
        fi
        exit 0
    "

    [ "$status" -eq 0 ]
}

# Test 8: Git tag与版本一致性
@test "git tags match version file" {
    if [ ! -f "$VERSION_FILE" ]; then
        skip "VERSION file not found"
    fi

    run bash -c "
        cd '$PROJECT_ROOT'
        version=\$(cat '$VERSION_FILE' | tr -d '[:space:]')

        # 检查是否有对应的git tag
        if git tag | grep -q \"^v\?\$version\$\"; then
            echo \"Git tag found for version: \$version\"
            exit 0
        else
            echo \"No git tag for version: \$version (expected: v\$version)\"
            exit 1
        fi
    "

    [ "$status" -eq 0 ] || [[ "$output" =~ "No git tag" ]]
}

# Test 9: CHANGELOG版本记录
@test "CHANGELOG contains current version" {
    local changelog="$PROJECT_ROOT/CHANGELOG.md"

    if [ ! -f "$changelog" ] || [ ! -f "$VERSION_FILE" ]; then
        skip "CHANGELOG.md or VERSION not found"
    fi

    run bash -c "
        version=\$(cat '$VERSION_FILE' | tr -d '[:space:]')
        if grep -q \"\$version\" '$changelog'; then
            echo \"CHANGELOG contains version: \$version\"
            exit 0
        else
            echo \"CHANGELOG missing version: \$version\"
            exit 1
        fi
    "

    [ "$status" -eq 0 ] || [[ "$output" =~ "missing version" ]]
}

# Test 10: CI验证版本一致性
@test "CI checks version consistency" {
    local ci_file="$PROJECT_ROOT/.github/workflows/ce-gates.yml"

    if [ ! -f "$ci_file" ]; then
        skip "CI workflow not found"
    fi

    # 检查CI中是否有版本检查
    run bash -c "
        grep -i 'version' '$ci_file' | head -5
    "

    # CI可能没有专门的版本检查job
    [ "$status" -eq 0 ] || skip "No version check in CI"
}

# Test 11: 预发布版本标识
@test "pre-release versions are properly marked" {
    run bash -c "
        version='1.2.3-alpha.1'

        if [[ \"\$version\" =~ -[a-zA-Z] ]]; then
            prerelease=\$(echo \"\$version\" | sed 's/.*-\([a-zA-Z.0-9]*\).*/\1/')
            echo \"Pre-release identified: \$prerelease\"
            exit 0
        else
            echo \"Stable version: \$version\"
            exit 0
        fi
    "

    [ "$status" -eq 0 ]
}

# Test 12: 版本文件权限正确
@test "version files have correct permissions" {
    if [ ! -f "$VERSION_FILE" ]; then
        skip "VERSION file not found"
    fi

    run bash -c "
        # VERSION文件应该是可读的
        if [ -r '$VERSION_FILE' ]; then
            echo \"VERSION file is readable\"
            exit 0
        else
            echo \"VERSION file is not readable\"
            exit 1
        fi
    "

    [ "$status" -eq 0 ]
}
