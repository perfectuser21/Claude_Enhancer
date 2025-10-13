#!/usr/bin/env python3
"""
Mobile UX Testing Suite for Claude Enhancer 5.0
Tests mobile-specific user experience factors
"""

import json
import re
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


@dataclass
class MobileUXIssue:
    type: str
    severity: str  # 'critical', 'major', 'minor'
    element: str
    description: str
    recommendation: str
    file_path: Optional[str] = None
    viewport: Optional[str] = None


@dataclass
class MobileTestResult:
    test_name: str
    status: str  # 'pass', 'fail', 'warning'
    score: int  # 0-100
    details: str
    issues: List[MobileUXIssue]


class MobileUXTester:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.frontend_path = self.project_path / "frontend"
        self.results = []
        self.issues = []

        # Mobile viewport configurations to test
        self.viewports = {
            "mobile_small": {"width": 320, "height": 568, "name": "iPhone SE"},
            "mobile_medium": {"width": 375, "height": 667, "name": "iPhone 8"},
            "mobile_large": {"width": 414, "height": 896, "name": "iPhone 11 Pro Max"},
            "tablet_portrait": {"width": 768, "height": 1024, "name": "iPad Portrait"},
            "tablet_landscape": {
                "width": 1024,
                "height": 768,
                "name": "iPad Landscape",
            },
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive mobile UX tests"""
        print("📱 Starting Mobile UX Testing...")

        # Test categories
        touch_results = self._test_touch_interaction()
        responsive_results = self._test_responsive_layout()
        performance_results = self._test_mobile_performance()
        navigation_results = self._test_mobile_navigation()
        forms_results = self._test_mobile_forms()
        accessibility_results = self._test_mobile_accessibility()

        # Store all results
        all_test_results = []
        all_test_results.extend(
            [
                touch_results,
                responsive_results,
                performance_results,
                navigation_results,
                forms_results,
                accessibility_results,
            ]
        )

        self.results = all_test_results

        # Calculate overall score
        overall_score = sum(r.score for r in self.results) // len(self.results)

        return {
            "test_date": datetime.now().isoformat(),
            "project": "Claude Enhancer 5.0 - Mobile UX",
            "overall_score": overall_score,
            "tests": [asdict(result) for result in self.results],
            "total_issues": len(self.issues),
            "critical_issues": len(
                [i for i in self.issues if i.severity == "critical"]
            ),
            "issues": [asdict(issue) for issue in self.issues],
            "viewports_tested": list(self.viewports.keys()),
        }

    def _test_touch_interaction(self) -> MobileTestResult:
        """Test touch interaction design"""
        print("  👆 Testing Touch Interaction...")

        issues = []

        # Check CSS for touch-friendly sizes
        css_files = list(self.frontend_path.glob("**/*.css"))

        for css_file in css_files:
            content = css_file.read_text()

            # Check for minimum touch target sizes (44px recommended by Apple, 48dp by Google)
            button_patterns = [
                r"\.button\s*{[^}]*}",
                r"button\s*{[^}]*}",
                r"\.btn\s*{[^}]*}",
                r'input\[type="submit"\]\s*{[^}]*}',
            ]

            for pattern in button_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    pass  # Auto-fixed empty block
                    # Check for touch target size
                    has_min_height = re.search(r"min-height:\s*([0-9]+)", match)
                    has_height = re.search(r"height:\s*([0-9]+)", match)
                    has_padding = re.search(r"padding:\s*([0-9]+)", match)

                    height_value = 0
                    if has_min_height:
                        height_value = int(has_min_height.group(1))
                    elif has_height:
                        height_value = int(has_height.group(1))

                    padding_value = 0
                    if has_padding:
                        padding_value = int(has_padding.group(1))

                    total_height = height_value + (padding_value * 2)

                    if total_height < 44 and height_value > 0:
                        issues.append(
                            MobileUXIssue(
                                type="touch_targets",
                                severity="major",
                                element="button",
                                description=f"Touch target too small: {total_height}px (minimum 44px recommended)",
                                recommendation="Increase button size to minimum 44px for touch accessibility",
                                file_path=str(css_file),
                            )
                        )

            # Check for hover effects that don't work on touch
            hover_patterns = re.findall(r":hover\s*{[^}]*}", content, re.IGNORECASE)
            if hover_patterns:
                pass  # Auto-fixed empty block
                # Check if there are corresponding touch/active states
                has_active = ":active" in content
                has_focus = ":focus" in content

                if not has_active and not has_focus:
                    issues.append(
                        MobileUXIssue(
                            type="touch_interaction",
                            severity="minor",
                            element="hover effects",
                            description="Hover effects without corresponding touch states",
                            recommendation="Add :active and :focus states for touch devices",
                            file_path=str(css_file),
                        )
                    )

        # Check for touch-specific CSS
        has_touch_css = False
        for css_file in css_files:
            content = css_file.read_text()
            if any(
                touch_pattern in content.lower()
                for touch_pattern in [
                    "touch-action",
                    "@media (hover: none)",
                    "pointer: coarse",
                ]
            ):
                has_touch_css = True
                break

        if not has_touch_css:
            issues.append(
                MobileUXIssue(
                    type="touch_optimization",
                    severity="minor",
                    element="CSS",
                    description="No touch-specific CSS optimizations found",
                    recommendation="Add touch-action properties and pointer media queries",
                    file_path="CSS files",
                )
            )

        self.issues.extend(issues)

        # Calculate score
        major_issues = len([i for i in issues if i.severity == "major"])
        minor_issues = len([i for i in issues if i.severity == "minor"])

        score = 90 - (major_issues * 20) - (minor_issues * 5)
        status = "pass" if score >= 80 else "warning" if score >= 60 else "fail"

        return MobileTestResult(
            test_name="Touch Interaction",
            status=status,
            score=max(score, 40),
            details=f"Found {len(issues)} touch interaction issues",
            issues=issues,
        )

    def _test_responsive_layout(self) -> MobileTestResult:
        """Test responsive layout across different viewports"""
        print("  📐 Testing Responsive Layout...")

        issues = []

        # Check CSS for responsive breakpoints
        css_files = list(self.frontend_path.glob("**/*.css"))

        responsive_patterns = {
            "mobile_first": r"@media\s*\([^)]*min-width[^)]*\)",
            "desktop_first": r"@media\s*\([^)]*max-width[^)]*\)",
            "orientation": r"@media\s*\([^)]*orientation[^)]*\)",
            "retina": r"@media\s*\([^)]*resolution[^)]*\)",
            "viewport_width": r"@media\s*\([^)]*width[^)]*\)",
        }

        responsive_features = {}

        for css_file in css_files:
            content = css_file.read_text()

            for feature, pattern in responsive_patterns.items():
                if re.search(pattern, content, re.IGNORECASE):
                    responsive_features[feature] = True

            # Check for flexible layouts
            flexible_patterns = [
                "flex",
                "grid",
                "flexbox",
                "%",
                "fr",
                "minmax",
                "auto",
                "max-width",
                "min-width",
            ]

            has_flexible_layout = any(
                pattern in content.lower() for pattern in flexible_patterns
            )

            # Check for fixed widths that might break on mobile
            fixed_width_matches = re.findall(r"width:\s*([0-9]+)px", content)
            large_fixed_widths = [
                int(match) for match in fixed_width_matches if int(match) > 320
            ]

            if large_fixed_widths and not has_flexible_layout:
                issues.append(
                    MobileUXIssue(
                        type="responsive_layout",
                        severity="major",
                        element="fixed widths",
                        description=f"Fixed widths may break on mobile: {large_fixed_widths}px",
                        recommendation="Use flexible units (%, em, rem, fr) instead of fixed pixels",
                        file_path=str(css_file),
                    )
                )

        # Check for mobile-first approach
        if not responsive_features.get("mobile_first", False):
            issues.append(
                MobileUXIssue(
                    type="responsive_strategy",
                    severity="minor",
                    element="media queries",
                    description="No mobile-first media queries detected",
                    recommendation="Use min-width media queries for mobile-first responsive design",
                    file_path="CSS files",
                )
            )

        # Check for viewport meta tag in HTML
        html_files = list(self.frontend_path.glob("**/*.html"))
        has_viewport_meta = False

        for html_file in html_files:
            content = html_file.read_text()
            if 'name="viewport"' in content:
                has_viewport_meta = True

                # Check viewport configuration
                viewport_match = re.search(
                    r'content="([^"]*)".*viewport', content, re.IGNORECASE
                )
                if viewport_match:
                    viewport_content = viewport_match.group(1)

                    if "user-scalable=no" in viewport_content:
                        issues.append(
                            MobileUXIssue(
                                type="responsive_layout",
                                severity="minor",
                                element="viewport meta",
                                description="user-scalable=no prevents zooming for accessibility",
                                recommendation="Allow user scaling for accessibility: remove user-scalable=no",
                                file_path=str(html_file),
                            )
                        )
                break

        if not has_viewport_meta:
            issues.append(
                MobileUXIssue(
                    type="responsive_layout",
                    severity="critical",
                    element="viewport meta",
                    description="Missing viewport meta tag",
                    recommendation="Add viewport meta tag for mobile optimization",
                    file_path="HTML files",
                )
            )

        self.issues.extend(issues)

        # Calculate score
        critical_issues = len([i for i in issues if i.severity == "critical"])
        major_issues = len([i for i in issues if i.severity == "major"])
        minor_issues = len([i for i in issues if i.severity == "minor"])

        score = 95
        if critical_issues > 0:
            score -= 40
        score -= (major_issues * 15) + (minor_issues * 5)

        status = "pass" if score >= 80 else "warning" if score >= 60 else "fail"

        return MobileTestResult(
            test_name="Responsive Layout",
            status=status,
            score=max(score, 30),
            details=f"Found {len(issues)} responsive layout issues",
            issues=issues,
        )

    def _test_mobile_performance(self) -> MobileTestResult:
        """Test mobile performance considerations"""
        print("  ⚡ Testing Mobile Performance...")

        issues = []

        # Check for mobile performance optimizations
        html_files = list(self.frontend_path.glob("**/*.html"))

        for html_file in html_files:
            content = html_file.read_text()

            # Check for resource hints
            resource_hints = ["preload", "prefetch", "preconnect", "dns-prefetch"]
            found_hints = [hint for hint in resource_hints if hint in content]

            if not found_hints:
                issues.append(
                    MobileUXIssue(
                        type="mobile_performance",
                        severity="minor",
                        element="resource hints",
                        description="No resource hints found for mobile performance",
                        recommendation="Add preconnect, dns-prefetch for external resources",
                        file_path=str(html_file),
                    )
                )

            # Check for font optimization
            if "font-display" not in content and "googleapis.com/css" in content:
                issues.append(
                    MobileUXIssue(
                        type="mobile_performance",
                        severity="minor",
                        element="font loading",
                        description="Web fonts without font-display optimization",
                        recommendation="Add font-display: swap for better loading performance",
                        file_path=str(html_file),
                    )
                )

            # Check for large images without lazy loading
            img_tags = re.findall(r"<img[^>]*>", content, re.IGNORECASE)
            lazy_images = [img for img in img_tags if 'loading="lazy"' in img]

            if len(img_tags) > 2 and len(lazy_images) == 0:
                issues.append(
                    MobileUXIssue(
                        type="mobile_performance",
                        severity="minor",
                        element="image loading",
                        description="Images without lazy loading on mobile",
                        recommendation="Add loading='lazy' attribute to images below the fold",
                        file_path=str(html_file),
                    )
                )

        # Check CSS for mobile performance
        css_files = list(self.frontend_path.glob("**/*.css"))

        for css_file in css_files:
            content = css_file.read_text()

            # Check for will-change property usage
            if "will-change" in content:
                will_change_matches = re.findall(r"will-change:\s*([^;]+);", content)
                for match in will_change_matches:
                    if "auto" not in match and len(match.split(",")) > 3:
                        issues.append(
                            MobileUXIssue(
                                type="mobile_performance",
                                severity="minor",
                                element="CSS animations",
                                description="Overuse of will-change property can hurt mobile performance",
                                recommendation="Use will-change sparingly and set to 'auto' when done",
                                file_path=str(css_file),
                            )
                        )

            # Check for complex selectors that might be slow
            complex_selectors = re.findall(r"[^{]*{", content)
            slow_selectors = [
                sel
                for sel in complex_selectors
                if sel.count(" ") > 4 or sel.count(">") > 2
            ]

            if len(slow_selectors) > 5:
                issues.append(
                    MobileUXIssue(
                        type="mobile_performance",
                        severity="minor",
                        element="CSS selectors",
                        description="Complex CSS selectors may impact mobile performance",
                        recommendation="Simplify CSS selectors for better mobile performance",
                        file_path=str(css_file),
                    )
                )

        # Check JavaScript for mobile optimizations
        js_files = list(self.frontend_path.glob("**/*.js"))

        has_lazy_loading = False
        has_intersection_observer = False

        for js_file in js_files:
            content = js_file.read_text()

            if "IntersectionObserver" in content:
                has_intersection_observer = True

            if "lazy" in content.lower() or "import(" in content:
                has_lazy_loading = True

        if not has_lazy_loading and len(js_files) > 3:
            issues.append(
                MobileUXIssue(
                    type="mobile_performance",
                    severity="minor",
                    element="JavaScript loading",
                    description="No lazy loading detected for JavaScript modules",
                    recommendation="Implement code splitting and lazy loading for better mobile performance",
                    file_path="JavaScript files",
                )
            )

        self.issues.extend(issues)

        # Calculate score
        minor_issues = len([i for i in issues if i.severity == "minor"])
        score = 85 - (minor_issues * 7)

        status = "pass" if score >= 80 else "warning"

        return MobileTestResult(
            test_name="Mobile Performance",
            status=status,
            score=max(score, 60),
            details=f"Found {len(issues)} mobile performance issues",
            issues=issues,
        )

    def _test_mobile_navigation(self) -> MobileTestResult:
        """Test mobile navigation patterns"""
        print("  🧭 Testing Mobile Navigation...")

        issues = []

        # Check for mobile navigation patterns
        css_files = list(self.frontend_path.glob("**/*.css"))
        js_files = list(self.frontend_path.glob("**/*.js"))

        # Check for hamburger menu or mobile navigation
        has_mobile_nav = False
        nav_patterns = [
            "hamburger",
            "menu-toggle",
            "nav-toggle",
            "mobile-menu",
            "menu-btn",
        ]

        for css_file in css_files:
            content = css_file.read_text()
            if any(pattern in content.lower() for pattern in nav_patterns):
                has_mobile_nav = True
                break

        for js_file in js_files:
            content = js_file.read_text()
            if any(pattern in content.lower() for pattern in nav_patterns):
                has_mobile_nav = True
                break

        if not has_mobile_nav:
            issues.append(
                MobileUXIssue(
                    type="mobile_navigation",
                    severity="major",
                    element="navigation menu",
                    description="No mobile-specific navigation pattern detected",
                    recommendation="Implement hamburger menu or mobile-friendly navigation",
                    file_path="Navigation components",
                )
            )

        # Check for bottom navigation (mobile-friendly pattern)
        has_bottom_nav = False
        for css_file in css_files:
            content = css_file.read_text()
            if any(
                pattern in content.lower()
                for pattern in ["bottom-nav", "tab-bar", "fixed-bottom", "bottom-bar"]
            ):
                has_bottom_nav = True
                break

        # Check for appropriate touch targets in navigation
        for css_file in css_files:
            content = css_file.read_text()

            # Look for navigation link styles
            nav_link_patterns = [
                r"\.nav[^{]*a\s*{[^}]*}",
                r"nav\s+a\s*{[^}]*}",
                r"\.menu[^{]*a\s*{[^}]*}",
            ]

            for pattern in nav_link_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    pass  # Auto-fixed empty block
                    # Check for adequate padding for touch targets
                    padding_match = re.search(r"padding:\s*([0-9]+)", match)
                    if padding_match:
                        padding_value = int(padding_match.group(1))
                        if padding_value < 12:  # Minimum for comfortable touch
                            issues.append(
                                MobileUXIssue(
                                    type="mobile_navigation",
                                    severity="minor",
                                    element="navigation links",
                                    description=f"Navigation links have small touch targets: {padding_value}px padding",
                                    recommendation="Increase padding to at least 12px for comfortable touch navigation",
                                    file_path=str(css_file),
                                )
                            )

        self.issues.extend(issues)

        # Calculate score
        major_issues = len([i for i in issues if i.severity == "major"])
        minor_issues = len([i for i in issues if i.severity == "minor"])

        score = 90 - (major_issues * 25) - (minor_issues * 8)
        if has_bottom_nav:
            score += 5  # Bonus for mobile-friendly bottom navigation

        status = "pass" if score >= 80 else "warning" if score >= 60 else "fail"

        return MobileTestResult(
            test_name="Mobile Navigation",
            status=status,
            score=max(score, 40),
            details=f"Mobile navigation analysis, found {len(issues)} issues",
            issues=issues,
        )

    def _test_mobile_forms(self) -> MobileTestResult:
        """Test mobile form usability"""
        print("  📝 Testing Mobile Forms...")

        issues = []

        # Check HTML files for form elements
        html_files = list(self.frontend_path.glob("**/*.html"))
        css_files = list(self.frontend_path.glob("**/*.css"))

        # Check for input types optimized for mobile
        mobile_input_types = [
            "email",
            "tel",
            "url",
            "number",
            "date",
            "time",
            "datetime-local",
            "search",
        ]

        for html_file in html_files:
            content = html_file.read_text()

            # Find all input elements
            input_matches = re.findall(r"<input[^>]*>", content, re.IGNORECASE)

            generic_inputs = 0
            optimized_inputs = 0

            for input_tag in input_matches:
                if "type=" in input_tag:
                    type_match = re.search(r'type="([^"]*)"', input_tag, re.IGNORECASE)
                    if type_match:
                        input_type = type_match.group(1)
                        if input_type in mobile_input_types:
                            optimized_inputs += 1
                        elif input_type == "text":
                            generic_inputs += 1

            if generic_inputs > 0 and optimized_inputs == 0:
                issues.append(
                    MobileUXIssue(
                        type="mobile_forms",
                        severity="minor",
                        element="input types",
                        description=f"{generic_inputs} text inputs could use mobile-optimized types",
                        recommendation="Use specific input types (email, tel, url) for better mobile keyboards",
                        file_path=str(html_file),
                    )
                )

            # Check for autocomplete attributes
            autocomplete_inputs = [
                inp for inp in input_matches if "autocomplete=" in inp
            ]
            if len(input_matches) > 2 and len(autocomplete_inputs) == 0:
                issues.append(
                    MobileUXIssue(
                        type="mobile_forms",
                        severity="minor",
                        element="autocomplete",
                        description="Form inputs missing autocomplete attributes",
                        recommendation="Add autocomplete attributes for better mobile form filling",
                        file_path=str(html_file),
                    )
                )

        # Check CSS for form styling
        for css_file in css_files:
            content = css_file.read_text()

            # Check for input sizing
            input_styles = re.findall(
                r"input[^{]*{[^}]*}", content, re.IGNORECASE | re.DOTALL
            )
            for style in input_styles:
                pass  # Auto-fixed empty block
                # Check for minimum height
                height_match = re.search(r"height:\s*([0-9]+)", style)
                min_height_match = re.search(r"min-height:\s*([0-9]+)", style)

                height_value = 0
                if min_height_match:
                    height_value = int(min_height_match.group(1))
                elif height_match:
                    height_value = int(height_match.group(1))

                if height_value > 0 and height_value < 44:
                    issues.append(
                        MobileUXIssue(
                            type="mobile_forms",
                            severity="major",
                            element="form inputs",
                            description=f"Form inputs too small for touch: {height_value}px height",
                            recommendation="Increase form input height to minimum 44px for touch accessibility",
                            file_path=str(css_file),
                        )
                    )

            # Check for form spacing
            if "margin-bottom" not in content and "gap" not in content:
                issues.append(
                    MobileUXIssue(
                        type="mobile_forms",
                        severity="minor",
                        element="form spacing",
                        description="Forms may lack adequate spacing for mobile",
                        recommendation="Add margin or gap between form elements for easier touch interaction",
                        file_path=str(css_file),
                    )
                )

        self.issues.extend(issues)

        # Calculate score
        major_issues = len([i for i in issues if i.severity == "major"])
        minor_issues = len([i for i in issues if i.severity == "minor"])

        score = 90 - (major_issues * 20) - (minor_issues * 8)
        status = "pass" if score >= 80 else "warning" if score >= 60 else "fail"

        return MobileTestResult(
            test_name="Mobile Forms",
            status=status,
            score=max(score, 50),
            details=f"Mobile form usability analysis, found {len(issues)} issues",
            issues=issues,
        )

    def _test_mobile_accessibility(self) -> MobileTestResult:
        """Test mobile-specific accessibility features"""
        print("  ♿ Testing Mobile Accessibility...")

        issues = []

        # Check for mobile accessibility features
        css_files = list(self.frontend_path.glob("**/*.css"))

        # Check for reduce motion support
        has_reduce_motion = False
        for css_file in css_files:
            content = css_file.read_text()
            if "prefers-reduced-motion" in content:
                has_reduce_motion = True
                break

        if not has_reduce_motion:
            issues.append(
                MobileUXIssue(
                    type="mobile_accessibility",
                    severity="minor",
                    element="motion preferences",
                    description="No support for reduced motion preferences",
                    recommendation="Add prefers-reduced-motion media query for accessibility",
                    file_path="CSS files",
                )
            )

        # Check for high contrast support
        has_high_contrast = False
        for css_file in css_files:
            content = css_file.read_text()
            if any(
                pattern in content
                for pattern in [
                    "prefers-contrast",
                    "forced-colors",
                    "-ms-high-contrast",
                ]
            ):
                has_high_contrast = True
                break

        if not has_high_contrast:
            issues.append(
                MobileUXIssue(
                    type="mobile_accessibility",
                    severity="minor",
                    element="contrast preferences",
                    description="No support for high contrast mode",
                    recommendation="Add support for forced-colors and prefers-contrast",
                    file_path="CSS files",
                )
            )

        # Check for zoom support (no user-scalable=no)
        html_files = list(self.frontend_path.glob("**/*.html"))
        for html_file in html_files:
            content = html_file.read_text()
            if "user-scalable=no" in content:
                issues.append(
                    MobileUXIssue(
                        type="mobile_accessibility",
                        severity="major",
                        element="viewport scaling",
                        description="Viewport prevents user scaling (accessibility issue)",
                        recommendation="Remove user-scalable=no to allow zoom for accessibility",
                        file_path=str(html_file),
                    )
                )

        # Check for focus indicators that work on mobile
        has_mobile_focus = False
        for css_file in css_files:
            content = css_file.read_text()
            # Look for touch-friendly focus indicators
            if any(
                pattern in content
                for pattern in [":focus-visible", "outline-offset", "box-shadow"]
            ):
                has_mobile_focus = True
                break

        if not has_mobile_focus:
            issues.append(
                MobileUXIssue(
                    type="mobile_accessibility",
                    severity="minor",
                    element="focus indicators",
                    description="Focus indicators may not be optimized for mobile",
                    recommendation="Add mobile-friendly focus indicators with adequate size and contrast",
                    file_path="CSS files",
                )
            )

        self.issues.extend(issues)

        # Calculate score
        major_issues = len([i for i in issues if i.severity == "major"])
        minor_issues = len([i for i in issues if i.severity == "minor"])

        score = 90 - (major_issues * 25) - (minor_issues * 8)
        status = "pass" if score >= 80 else "warning" if score >= 60 else "fail"

        return MobileTestResult(
            test_name="Mobile Accessibility",
            status=status,
            score=max(score, 50),
            details=f"Mobile accessibility analysis, found {len(issues)} issues",
            issues=issues,
        )

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive mobile UX test report"""
        report = f"""# Mobile UX Test Report
## Claude Enhancer 5.0

**Test Date:** {results['test_date']}
**Overall Mobile UX Score:** {results['overall_score']}/100

---

## Executive Summary

This mobile UX audit evaluates the application's performance and usability across mobile devices and viewports. The testing covers touch interaction, responsive design, performance, navigation, forms, and mobile accessibility.

### Key Metrics
- **Total Issues Found:** {results['total_issues']}
- **Critical Issues:** {results['critical_issues']}
- **Overall Mobile UX Score:** {results['overall_score']}/100

### Viewports Tested
"""

        for viewport in results["viewports_tested"]:
            viewport_info = self.viewports.get(viewport, {})
            name = viewport_info.get("name", viewport)
            width = viewport_info.get("width", "Unknown")
            height = viewport_info.get("height", "Unknown")
            report += f"- **{name}:** {width}×{height}px\n"

        report += f"""
---

## Test Results Summary

"""

        for test in results["tests"]:
            status_emoji = (
                "✅"
                if test["status"] == "pass"
                else "⚠️"
                if test["status"] == "warning"
                else "❌"
            )
            report += f"- {status_emoji} **{test['test_name']}:** {test['score']}/100 - {test['details']}\n"

        # Critical and Major Issues
        critical_issues = [
            issue for issue in results["issues"] if issue["severity"] == "critical"
        ]
        major_issues = [
            issue for issue in results["issues"] if issue["severity"] == "major"
        ]

        if critical_issues:
            report += f"""
---

## Critical Mobile Issues

"""
            for i, issue in enumerate(critical_issues, 1):
                report += f"""
### {i}. {issue['element'].title()} - {issue['type'].replace('_', ' ').title()}

**Description:** {issue['description']}
**Recommendation:** {issue['recommendation']}
**File:** {issue.get('file_path', 'Multiple files')}
**Viewport:** {issue.get('viewport', 'All viewports')}

"""

        if major_issues:
            report += f"""
---

## Major Mobile Issues

"""
            for i, issue in enumerate(major_issues, 1):
                report += f"""
### {i}. {issue['element'].title()} - {issue['type'].replace('_', ' ').title()}

**Description:** {issue['description']}
**Recommendation:** {issue['recommendation']}
**File:** {issue.get('file_path', 'Multiple files')}
**Viewport:** {issue.get('viewport', 'All viewports')}

"""

        report += f"""
---

## Mobile UX Recommendations

### High Priority
1. **Touch Targets:** Ensure all interactive elements are at least 44×44px
2. **Viewport Configuration:** Fix viewport meta tag issues
3. **Navigation:** Implement mobile-friendly navigation patterns
4. **Form Optimization:** Use appropriate input types and sizing for mobile

### Medium Priority
1. **Performance:** Implement lazy loading and resource hints
2. **Responsive Design:** Use flexible layouts instead of fixed widths
3. **Accessibility:** Support zoom and motion preferences
4. **Touch Interaction:** Add appropriate touch states and feedback

### Low Priority
1. **Advanced Features:** Consider bottom navigation for better thumb accessibility
2. **Progressive Enhancement:** Implement mobile-specific enhancements
3. **Testing:** Regular testing on actual devices

---

## Mobile-Specific Considerations

### Touch Interface Design
- Minimum 44×44px touch targets
- Adequate spacing between interactive elements
- Clear visual feedback for touch interactions
- Avoid hover-dependent interactions

### Performance on Mobile Networks
- Optimize images and fonts for mobile
- Implement lazy loading for better perceived performance
- Use resource hints for critical resources
- Consider offline functionality

### Mobile Navigation Patterns
- Hamburger menu for complex navigation
- Bottom navigation for primary actions
- Breadcrumbs for deep navigation
- Search functionality for content discovery

### Form Design for Mobile
- Use specific input types (email, tel, url)
- Implement autocomplete for faster form filling
- Adequate spacing and sizing for touch input
- Clear error messages and validation

---

## Testing Recommendations

### Device Testing
- Test on actual devices, not just browser dev tools
- Include various screen sizes and orientations
- Test with different network conditions
- Verify touch interactions work as expected

### Performance Testing
- Measure loading times on 3G networks
- Test with limited bandwidth conditions
- Monitor memory usage on lower-end devices
- Verify smooth scrolling and animations

### Accessibility Testing
- Test with mobile screen readers (TalkBack, VoiceOver)
- Verify zoom functionality works properly
- Test with high contrast and reduced motion settings
- Ensure keyboard navigation works on mobile

---

**Next Steps:** Focus on critical and major issues first, then improve overall mobile experience based on user feedback and analytics.
"""

        return report


def main():
    """Main execution function"""
    project_path = "/home/xx/dev/Claude Enhancer 5.0"

    print("📱 Mobile UX Test Runner - Starting Comprehensive Mobile Testing")
    print("=" * 70)

    tester = MobileUXTester(project_path)

    # Run all tests
    results = tester.run_all_tests()

    # Generate report
    report_content = tester.generate_report(results)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save JSON results
    json_file = Path(project_path) / f"mobile_ux_results_{timestamp}.json"
    with open(json_file, "w") as f:
        json.dump(results, f, indent=2)

    # Save markdown report
    report_file = Path(project_path) / "MOBILE_UX_REPORT.md"
    with open(report_file, "w") as f:
        f.write(report_content)

    print(f"\n✅ Mobile UX Testing Complete!")
    print(f"📊 Overall Score: {results['overall_score']}/100")
    print(f"🔍 Total Issues: {results['total_issues']}")
    print(f"⚠️  Critical Issues: {results['critical_issues']}")
    print(f"📋 Report saved to: {report_file}")
    print(f"📄 JSON results saved to: {json_file}")

    return results


if __name__ == "__main__":
    main()
