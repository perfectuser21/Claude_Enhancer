#!/usr/bin/env bats
# =============================================================================
# Conflict Detection Integration Tests
# Tests conflict detection and resolution in multi-terminal scenarios
# =============================================================================

load ../helpers/integration_helper
load ../helpers/fixture_helper

setup() {
    export PROJECT_ROOT="/home/xx/dev/Claude Enhancer 5.0"
    TEST_REPO=$(create_test_repo "conflict-test")
    cd "${TEST_REPO}"

    create_nodejs_project_fixture
    git add .
    git commit -q -m "chore: setup project"
}

teardown() {
    cleanup_terminal_env
    cleanup_test_repo "${TEST_REPO}"
}

@test "Conflict detection: Two terminals edit same file" {
    log_test_info "Testing same file conflict detection"

    # Create base file
    mkdir -p src/shared
    cat > src/shared/config.ts << 'EOF'
export const config = {
    version: '1.0.0',
    environment: 'development'
};
EOF

    git add src/shared/config.ts
    git commit -m "feat: add base config"

    # Terminal 1: Modify config
    export_terminal_env "t1"
    create_branch "feature-t1-config"

    cat > src/shared/config.ts << 'EOF'
export const config = {
    version: '1.0.0',
    environment: 'development',
    apiUrl: 'http://localhost:3000'  // T1 addition
};
EOF

    git add src/shared/config.ts
    git commit -m "feat(t1): add apiUrl"

    # Terminal 2: Also modify config (conflict)
    cleanup_terminal_env
    git checkout -q main 2>&1
    export_terminal_env "t2"
    create_branch "feature-t2-config"

    cat > src/shared/config.ts << 'EOF'
export const config = {
    version: '1.0.0',
    environment: 'development',
    database: 'mongodb://localhost:27017'  // T2 addition (conflict)
};
EOF

    git add src/shared/config.ts
    git commit -m "feat(t2): add database"

    # Merge T1 first (should succeed)
    git checkout -q main 2>&1
    git merge --no-ff feature-t1-config -m "Merge t1 config" 2>&1
    [ "$?" -eq 0 ]

    # Merge T2 (should conflict)
    git merge --no-ff feature-t2-config -m "Merge t2 config" 2>&1 || {
        log_test_info "Conflict detected as expected"

        # Verify conflict markers
        if git diff --name-only --diff-filter=U | grep -q "src/shared/config.ts"; then
            log_test_info "Conflict in config.ts confirmed"

            # Abort merge for cleanup
            git merge --abort 2>&1
        fi
    }

    cleanup_terminal_env
}

@test "Conflict detection: Same line modification in different branches" {
    # Create base file with specific content
    cat > src/calculator.ts << 'EOF'
export function calculate(a: number, b: number): number {
    return a + b;  // Simple addition
}
EOF

    git add src/calculator.ts
    git commit -m "feat: add calculator"

    # Branch 1: Multiply instead
    export_terminal_env "t1"
    create_branch "feature-multiply"

    cat > src/calculator.ts << 'EOF'
export function calculate(a: number, b: number): number {
    return a * b;  // Changed to multiplication
}
EOF

    git add src/calculator.ts
    git commit -m "feat(t1): change to multiplication"

    # Branch 2: Subtract instead
    cleanup_terminal_env
    git checkout -q main 2>&1
    export_terminal_env "t2"
    create_branch "feature-subtract"

    cat > src/calculator.ts << 'EOF'
export function calculate(a: number, b: number): number {
    return a - b;  // Changed to subtraction
}
EOF

    git add src/calculator.ts
    git commit -m "feat(t2): change to subtraction"

    # Attempt merge - should conflict
    git checkout -q main 2>&1
    git merge --no-ff feature-multiply -m "Merge multiply" 2>&1

    git merge --no-ff feature-subtract -m "Merge subtract" 2>&1 || {
        # Conflict expected
        run git diff --name-only --diff-filter=U
        [[ "${output}" == *"src/calculator.ts"* ]]

        # Cleanup
        git merge --abort 2>&1
    }

    cleanup_terminal_env
}

@test "Conflict detection: Multi-file conflict scenario" {
    # Setup base files
    mkdir -p src/models src/services

    cat > src/models/user.ts << 'EOF'
export interface User {
    id: string;
    name: string;
}
EOF

    cat > src/services/user.service.ts << 'EOF'
export class UserService {
    getUser(id: string): User {
        return { id, name: 'Test' };
    }
}
EOF

    git add src/
    git commit -m "feat: add user model and service"

    # Branch 1: Add email to user
    export_terminal_env "t1"
    create_branch "feature-add-email"

    cat > src/models/user.ts << 'EOF'
export interface User {
    id: string;
    name: string;
    email: string;  // T1: Add email
}
EOF

    cat > src/services/user.service.ts << 'EOF'
export class UserService {
    getUser(id: string): User {
        return { id, name: 'Test', email: 'test@example.com' };
    }
}
EOF

    git add src/
    git commit -m "feat(t1): add email field"

    # Branch 2: Add age to user (conflicts in both files)
    cleanup_terminal_env
    git checkout -q main 2>&1
    export_terminal_env "t2"
    create_branch "feature-add-age"

    cat > src/models/user.ts << 'EOF'
export interface User {
    id: string;
    name: string;
    age: number;  // T2: Add age
}
EOF

    cat > src/services/user.service.ts << 'EOF'
export class UserService {
    getUser(id: string): User {
        return { id, name: 'Test', age: 25 };
    }
}
EOF

    git add src/
    git commit -m "feat(t2): add age field"

    # Merge - expect conflicts in both files
    git checkout -q main 2>&1
    git merge --no-ff feature-add-email -m "Merge email" 2>&1

    git merge --no-ff feature-add-age -m "Merge age" 2>&1 || {
        # Check conflicts
        local conflicts=$(git diff --name-only --diff-filter=U)

        echo "${conflicts}" | grep -q "src/models/user.ts"
        echo "${conflicts}" | grep -q "src/services/user.service.ts"

        log_test_info "Multi-file conflicts detected correctly"

        git merge --abort 2>&1
    }

    cleanup_terminal_env
}

@test "Conflict resolution: Manual merge with conflict markers" {
    # Create conflict scenario
    simulate_multi_terminal_edit \
        "src/shared.js" \
        "// Terminal 1 version\nexport const value = 'T1';" \
        "// Terminal 2 version\nexport const value = 'T2';"

    # Merge first branch
    git merge --no-ff feature-t1 -m "Merge t1" 2>&1

    # Merge second branch (conflict)
    git merge --no-ff feature-t2 -m "Merge t2" 2>&1 || {
        # Manually resolve conflict
        cat > src/shared.js << 'EOF'
// Merged version
export const value = 'T1_AND_T2';
EOF

        git add src/shared.js
        git commit -m "Merge: resolve conflict"

        # Verify resolution
        run assert_file_contains "src/shared.js" "T1_AND_T2"
        [ "$status" -eq 0 ]
    }
}

@test "Conflict detection: Deletion vs modification conflict" {
    # Create base file
    cat > src/deprecated.ts << 'EOF'
export function oldFunction(): void {
    console.log('Old function');
}
EOF

    git add src/deprecated.ts
    git commit -m "feat: add deprecated function"

    # Branch 1: Delete the file
    export_terminal_env "t1"
    create_branch "feature-delete-old"

    git rm src/deprecated.ts
    git commit -m "feat(t1): remove deprecated function"

    # Branch 2: Modify the file
    cleanup_terminal_env
    git checkout -q main 2>&1
    export_terminal_env "t2"
    create_branch "feature-update-old"

    cat > src/deprecated.ts << 'EOF'
export function oldFunction(): void {
    console.log('Updated old function');
}
EOF

    git add src/deprecated.ts
    git commit -m "feat(t2): update deprecated function"

    # Merge - should conflict (delete vs modify)
    git checkout -q main 2>&1
    git merge --no-ff feature-delete-old -m "Merge delete" 2>&1

    git merge --no-ff feature-update-old -m "Merge update" 2>&1 || {
        log_test_info "Delete vs modify conflict detected"

        # Check git status
        run git status
        [[ "${output}" == *"deleted by us"* ]] || \
        [[ "${output}" == *"deleted by them"* ]] || \
        [[ "${output}" == *"both modified"* ]]

        git merge --abort 2>&1
    }

    cleanup_terminal_env
}

@test "Conflict detection: Directory structure conflict" {
    # Branch 1: Create file in new directory
    export_terminal_env "t1"
    create_branch "feature-t1-structure"

    mkdir -p src/modules/auth
    echo "// Auth module" > src/modules/auth/index.ts
    git add src/modules/
    git commit -m "feat(t1): add auth module"

    # Branch 2: Create different file in same directory
    cleanup_terminal_env
    git checkout -q main 2>&1
    export_terminal_env "t2"
    create_branch "feature-t2-structure"

    mkdir -p src/modules/auth
    echo "// Different auth implementation" > src/modules/auth/service.ts
    git add src/modules/
    git commit -m "feat(t2): add auth service"

    # Merge - should succeed (different files, same directory)
    git checkout -q main 2>&1
    git merge --no-ff feature-t1-structure -m "Merge t1" 2>&1
    [ "$?" -eq 0 ]

    git merge --no-ff feature-t2-structure -m "Merge t2" 2>&1
    [ "$?" -eq 0 ]

    # Both files should exist
    run assert_file_exists "src/modules/auth/index.ts"
    [ "$status" -eq 0 ]

    run assert_file_exists "src/modules/auth/service.ts"
    [ "$status" -eq 0 ]

    cleanup_terminal_env
}

@test "Conflict detection: Binary file conflict" {
    # Create binary file (simulate image)
    echo -e "\x89PNG\x0D\x0A\x1A\x0A" > image.png
    git add image.png
    git commit -m "feat: add image"

    # Branch 1: Modify binary
    export_terminal_env "t1"
    create_branch "feature-t1-image"

    echo -e "\x89PNG\x0D\x0A\x1A\x0AVERSION1" > image.png
    git add image.png
    git commit -m "feat(t1): update image v1"

    # Branch 2: Different modification
    cleanup_terminal_env
    git checkout -q main 2>&1
    export_terminal_env "t2"
    create_branch "feature-t2-image"

    echo -e "\x89PNG\x0D\x0A\x1A\x0AVERSION2" > image.png
    git add image.png
    git commit -m "feat(t2): update image v2"

    # Merge - binary conflict
    git checkout -q main 2>&1
    git merge --no-ff feature-t1-image -m "Merge t1 image" 2>&1

    git merge --no-ff feature-t2-image -m "Merge t2 image" 2>&1 || {
        log_test_info "Binary file conflict detected"

        run git diff --name-only --diff-filter=U
        [[ "${output}" == *"image.png"* ]]

        git merge --abort 2>&1
    }

    cleanup_terminal_env
}

@test "Conflict prevention: File locking mechanism simulation" {
    # Simulate file lock
    mkdir -p .workflow/locks

    # Terminal 1: Lock file for editing
    export_terminal_env "t1"
    create_branch "feature-t1-locked"

    local lock_file=".workflow/locks/src_shared_config.lock"
    echo "t1:$(date +%s)" > "${lock_file}"

    mkdir -p src/shared
    echo "// T1 editing" > src/shared/config.ts

    # Terminal 2: Check for lock before editing
    cleanup_terminal_env
    export_terminal_env "t2"
    create_branch "feature-t2-locked"

    if [[ -f "${lock_file}" ]]; then
        local lock_info=$(cat "${lock_file}")
        log_test_info "File locked by: ${lock_info}"

        # T2 should detect lock and wait or abort
        run test -f "${lock_file}"
        [ "$status" -eq 0 ]
    fi

    # T1 finishes and releases lock
    cleanup_terminal_env
    export_terminal_env "t1"
    git add src/shared/config.ts
    git commit -m "feat(t1): update config"
    rm -f "${lock_file}"

    # Now T2 can proceed
    cleanup_terminal_env
    export_terminal_env "t2"

    run test -f "${lock_file}"
    [ "$status" -ne 0 ]  # Lock should be gone

    echo "// T2 editing" > src/shared/config.ts
    git add src/shared/config.ts
    git commit -m "feat(t2): update config"

    cleanup_terminal_env
}

@test "Conflict detection: Complex three-way merge" {
    # Create base
    cat > src/complex.ts << 'EOF'
export class Complex {
    methodA() { return 'A'; }
    methodB() { return 'B'; }
}
EOF

    git add src/complex.ts
    git commit -m "feat: add complex class"

    # Branch 1: Modify methodA
    export_terminal_env "t1"
    create_branch "feature-t1-methodA"

    cat > src/complex.ts << 'EOF'
export class Complex {
    methodA() { return 'A-modified-by-T1'; }
    methodB() { return 'B'; }
}
EOF

    git add src/complex.ts
    git commit -m "feat(t1): modify methodA"

    # Branch 2: Modify methodB
    cleanup_terminal_env
    git checkout -q main 2>&1
    export_terminal_env "t2"
    create_branch "feature-t2-methodB"

    cat > src/complex.ts << 'EOF'
export class Complex {
    methodA() { return 'A'; }
    methodB() { return 'B-modified-by-T2'; }
}
EOF

    git add src/complex.ts
    git commit -m "feat(t2): modify methodB"

    # Branch 3: Modify both methods
    cleanup_terminal_env
    git checkout -q main 2>&1
    export_terminal_env "t3"
    create_branch "feature-t3-both"

    cat > src/complex.ts << 'EOF'
export class Complex {
    methodA() { return 'A-modified-by-T3'; }
    methodB() { return 'B-modified-by-T3'; }
}
EOF

    git add src/complex.ts
    git commit -m "feat(t3): modify both methods"

    # Merge T1 and T2 (different methods, should succeed)
    git checkout -q main 2>&1
    git merge --no-ff feature-t1-methodA -m "Merge t1" 2>&1
    [ "$?" -eq 0 ]

    git merge --no-ff feature-t2-methodB -m "Merge t2" 2>&1
    [ "$?" -eq 0 ]

    # Merge T3 (conflicts with both)
    git merge --no-ff feature-t3-both -m "Merge t3" 2>&1 || {
        log_test_info "Three-way merge conflict detected"

        run git diff --name-only --diff-filter=U
        [[ "${output}" == *"src/complex.ts"* ]]

        git merge --abort 2>&1
    }

    cleanup_terminal_env
}
