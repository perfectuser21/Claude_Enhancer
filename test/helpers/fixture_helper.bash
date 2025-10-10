#!/bin/bash
# =============================================================================
# Test Fixture Helpers
# Provides pre-built test data and scenarios
# =============================================================================

# Project fixtures
create_nodejs_project_fixture() {
    cat > package.json << 'EOF'
{
  "name": "test-project",
  "version": "1.0.0",
  "description": "Test project for integration tests",
  "main": "src/index.js",
  "scripts": {
    "test": "jest",
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "express": "^4.18.0"
  },
  "devDependencies": {
    "jest": "^29.0.0",
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0"
  }
}
EOF

    cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true
  }
}
EOF
}

create_python_project_fixture() {
    cat > requirements.txt << 'EOF'
flask==2.3.0
pytest==7.4.0
black==23.7.0
pylint==2.17.0
EOF

    cat > setup.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name="test-project",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "flask>=2.3.0",
    ],
)
EOF
}

# Source code fixtures
create_auth_module_fixture() {
    mkdir -p src/auth

    cat > src/auth/login.ts << 'EOF'
import { User } from '../models/User';
import { hashPassword, verifyPassword } from '../utils/crypto';

export class LoginService {
    async login(email: string, password: string): Promise<string> {
        const user = await User.findByEmail(email);

        if (!user) {
            throw new Error('User not found');
        }

        const isValid = await verifyPassword(password, user.passwordHash);

        if (!isValid) {
            throw new Error('Invalid password');
        }

        return generateToken(user);
    }

    async logout(token: string): Promise<void> {
        await invalidateToken(token);
    }
}
EOF

    cat > src/auth/auth.service.ts << 'EOF'
export interface IAuthService {
    authenticate(token: string): Promise<boolean>;
    authorize(userId: string, resource: string): Promise<boolean>;
}

export class AuthService implements IAuthService {
    async authenticate(token: string): Promise<boolean> {
        // TODO: Implement JWT validation
        return true;
    }

    async authorize(userId: string, resource: string): Promise<boolean> {
        // TODO: Implement RBAC check
        return true;
    }
}
EOF
}

create_test_suite_fixture() {
    mkdir -p test/auth

    cat > test/auth/login.test.ts << 'EOF'
import { LoginService } from '../../src/auth/login';

describe('LoginService', () => {
    let loginService: LoginService;

    beforeEach(() => {
        loginService = new LoginService();
    });

    test('should login with valid credentials', async () => {
        const token = await loginService.login('test@example.com', 'password123');
        expect(token).toBeDefined();
    });

    test('should throw error with invalid email', async () => {
        await expect(
            loginService.login('invalid@example.com', 'password123')
        ).rejects.toThrow('User not found');
    });

    test('should throw error with invalid password', async () => {
        await expect(
            loginService.login('test@example.com', 'wrongpassword')
        ).rejects.toThrow('Invalid password');
    });
});
EOF

    cat > test/auth/boundary.test.ts << 'EOF'
import { LoginService } from '../../src/auth/login';

describe('LoginService - Boundary Tests', () => {
    let loginService: LoginService;

    beforeEach(() => {
        loginService = new LoginService();
    });

    test('should handle empty email', async () => {
        await expect(
            loginService.login('', 'password123')
        ).rejects.toThrow();
    });

    test('should handle extremely long password', async () => {
        const longPassword = 'a'.repeat(10000);
        await expect(
            loginService.login('test@example.com', longPassword)
        ).rejects.toThrow();
    });

    test('should handle SQL injection attempts', async () => {
        await expect(
            loginService.login("'; DROP TABLE users; --", 'password')
        ).rejects.toThrow();
    });
});
EOF
}

# Git fixtures
create_git_history_fixture() {
    # Create a realistic git history
    for i in {1..5}; do
        echo "Feature ${i}" > "feature${i}.txt"
        git add "feature${i}.txt"
        git commit -q -m "feat: add feature ${i}"
    done

    # Create a development branch
    git checkout -q -b develop 2>&1
    echo "Development work" > dev.txt
    git add dev.txt
    git commit -q -m "feat: development work"

    git checkout -q main 2>&1
}

create_merge_conflict_scenario() {
    local file="$1"

    # Main branch version
    cat > "${file}" << 'EOF'
function calculate(a, b) {
    // Main branch implementation
    return a + b;
}
EOF
    git add "${file}"
    git commit -q -m "feat: add calculation function"

    # Feature branch 1
    git checkout -q -b feature-1 2>&1
    cat > "${file}" << 'EOF'
function calculate(a, b) {
    // Feature 1 implementation with validation
    if (typeof a !== 'number' || typeof b !== 'number') {
        throw new Error('Invalid input');
    }
    return a + b;
}
EOF
    git add "${file}"
    git commit -q -m "feat: add input validation"

    # Feature branch 2
    git checkout -q main 2>&1
    git checkout -q -b feature-2 2>&1
    cat > "${file}" << 'EOF'
function calculate(a, b) {
    // Feature 2 implementation with logging
    console.log('Calculating:', a, '+', b);
    return a + b;
}
EOF
    git add "${file}"
    git commit -q -m "feat: add logging"

    git checkout -q main 2>&1
}

# Workflow state fixtures
create_p1_complete_state() {
    set_phase "P1"
    create_plan_document
    commit_file "docs/PLAN.md" "docs: add feature plan"
    create_gate "01" "P1"
}

create_p2_complete_state() {
    create_p1_complete_state
    set_phase "P2"

    create_skeleton_notes
    mkdir -p src/auth src/models src/utils
    touch src/auth/login.ts src/auth/auth.service.ts

    git add src/ docs/SKELETON-NOTES.md
    git commit -q -m "feat: create skeleton structure"
    create_gate "02" "P2"
}

create_p3_complete_state() {
    create_p2_complete_state
    set_phase "P3"

    create_auth_module_fixture
    create_changelog

    git add src/ docs/CHANGELOG.md
    git commit -q -m "feat: implement auth module"
    create_gate "03" "P3"
}

create_p4_complete_state() {
    create_p3_complete_state
    set_phase "P4"

    create_test_suite_fixture
    create_test_report

    git add test/ docs/TEST-REPORT.md
    git commit -q -m "test: add comprehensive test suite"
    create_gate "04" "P4"
}

create_p5_complete_state() {
    create_p4_complete_state
    set_phase "P5"

    create_review_document

    git add docs/REVIEW.md
    git commit -q -m "docs: add code review"
    create_gate "05" "P5"
}

# Error scenarios
create_incomplete_plan_fixture() {
    cat > docs/PLAN.md << 'EOF'
# Incomplete Plan

## 任务清单
1. Task 1
2. Task 2
# Missing tasks - should have at least 5

## 受影响文件清单
# Missing file list

## 回滚方案
# Missing rollback plan
EOF
}

create_security_violation_fixture() {
    mkdir -p src/config

    cat > src/config/secrets.ts << 'EOF'
export const config = {
    apiKey: "sk-1234567890abcdef",
    password: "admin123",
    awsAccessKey: "AKIAIOSFODNN7EXAMPLE",
    awsSecretKey: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    privateKey: "-----BEGIN RSA PRIVATE KEY-----\nMIIBOgIBAAJBAKj34GkxFhD90vcNLYLInFEX6Ppy1tPf9Cnzj4p4WGeKLs1Pt8Qu\n-----END RSA PRIVATE KEY-----"
};
EOF
}

create_path_violation_fixture() {
    local phase="$1"

    case "${phase}" in
        P1)
            # P1 should only modify docs/PLAN.md
            mkdir -p src
            echo "console.log('unauthorized');" > src/unauthorized.js
            ;;
        P2)
            # P2 should not modify README
            cat > docs/README.md << 'EOF'
# Unauthorized README change in P2
EOF
            ;;
        P3)
            # P3 should not modify test files
            mkdir -p test
            echo "// unauthorized test" > test/unauthorized.test.js
            ;;
    esac
}

# Performance test fixtures
create_large_file_set() {
    local count="${1:-100}"

    mkdir -p src/generated
    for i in $(seq 1 "${count}"); do
        cat > "src/generated/module${i}.ts" << EOF
export class Module${i} {
    private value: number = ${i};

    getValue(): number {
        return this.value;
    }

    setValue(val: number): void {
        this.value = val;
    }
}
EOF
    done
}

create_complex_git_history() {
    local branch_count="${1:-10}"
    local commits_per_branch="${2:-5}"

    for branch in $(seq 1 "${branch_count}"); do
        git checkout -q -b "feature-${branch}" main 2>&1

        for commit in $(seq 1 "${commits_per_branch}"); do
            echo "Commit ${commit} on branch ${branch}" > "file-${branch}-${commit}.txt"
            git add "file-${branch}-${commit}.txt"
            git commit -q -m "feat: branch ${branch} commit ${commit}"
        done

        git checkout -q main 2>&1
        git merge -q --no-ff "feature-${branch}" -m "Merge feature-${branch}" 2>&1
    done
}

# CI/CD fixtures
create_github_actions_fixture() {
    mkdir -p .github/workflows

    cat > .github/workflows/ci.yml << 'EOF'
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: 18

    - name: Install dependencies
      run: npm ci

    - name: Run tests
      run: npm test

    - name: Build
      run: npm run build
EOF
}

# Database migration fixtures
create_migration_fixture() {
    mkdir -p migrations

    cat > migrations/001_create_users.sql << 'EOF'
-- Migration: Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rollback
-- DROP TABLE users;
EOF

    cat > migrations/002_add_roles.sql << 'EOF'
-- Migration: Add roles table
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE user_roles (
    user_id INTEGER REFERENCES users(id),
    role_id INTEGER REFERENCES roles(id),
    PRIMARY KEY (user_id, role_id)
);

-- Rollback
-- DROP TABLE user_roles;
-- DROP TABLE roles;
EOF
}

# Export fixture functions
export -f create_nodejs_project_fixture
export -f create_python_project_fixture
export -f create_auth_module_fixture
export -f create_test_suite_fixture
export -f create_git_history_fixture
export -f create_merge_conflict_scenario
export -f create_p1_complete_state
export -f create_p2_complete_state
export -f create_p3_complete_state
export -f create_p4_complete_state
export -f create_p5_complete_state
export -f create_incomplete_plan_fixture
export -f create_security_violation_fixture
export -f create_path_violation_fixture
export -f create_large_file_set
export -f create_complex_git_history
export -f create_github_actions_fixture
export -f create_migration_fixture
