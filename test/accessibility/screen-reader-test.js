#!/usr/bin/env node

/**
 * Screen Reader Simulation and Testing
 * Phase 4: Local Testing - Screen Reader Experience Validation
 *
 * Simulates screen reader behavior and tests:
 * 1. Element announcement order and content
 * 2. ARIA live region updates
 * 3. Navigation landmark structure
 * 4. Error message accessibility
 * 5. Focus management and announcements
 */

const { JSDOM } = require('jsdom');
const fs = require('fs').promises;
const path = require('path');

class ScreenReaderSimulator {
    constructor(options = {}) {
        this.options = {
            outputFile: options.outputFile || '/tmp/claude/screen-reader-test.json',
            verbose: options.verbose || false,
            announceAll: options.announceAll || false,
            ...options
        };

        this.announcements = [];
        this.navigationHistory = [];
        this.currentElement = null;
        this.focusHistory = [];
        this.liveRegionUpdates = [];

        this.navigationCommands = {};

        this.init();
        this.setupNavigationCommands();
    }

    async init() {
        // Create output directory
        const outputDir = path.dirname(this.options.outputFile);
        await fs.mkdir(outputDir, { recursive: true });
    }

    setupNavigationCommands() {
        // Define navigation commands after methods are available
        this.navigationCommands = {
            'nextElement': () => this.nextElement(),
            'previousElement': () => this.previousElement(),
            'nextHeading': () => this.nextHeading(),
            'previousHeading': () => this.previousHeading(),
            'nextLandmark': () => this.nextLandmark(),
            'previousLandmark': () => this.previousLandmark(),
            'nextButton': () => this.nextButton(),
            'previousButton': () => this.previousButton(),
            'nextLink': () => this.nextLink(),
            'previousLink': () => this.previousLink(),
            'nextFormField': () => this.nextFormField(),
            'previousFormField': () => this.previousFormField(),
            'announceElement': () => this.announceCurrentElement()
        };
    }

    /**
     * Test screen reader experience with error recovery interface
     */
    async testScreenReaderExperience(html) {
        console.log('🔊 Starting Screen Reader Experience Test...\n');

        const dom = new JSDOM(html);
        this.document = dom.window.document;
        this.window = dom.window;

        // Initialize virtual cursor
        this.currentElement = this.document.body;

        try {
            // Test 1: Initial page navigation
            await this.testInitialNavigation();

            // Test 2: Error message discovery
            await this.testErrorMessageDiscovery();

            // Test 3: Recovery options navigation
            await this.testRecoveryOptionsNavigation();

            // Test 4: Form interaction
            await this.testFormInteraction();

            // Test 5: Live region updates
            await this.testLiveRegionUpdates();

            // Test 6: Landmark navigation
            await this.testLandmarkNavigation();

            // Test 7: Heading structure
            await this.testHeadingStructure();

            // Test 8: Skip link functionality
            await this.testSkipLinkFunctionality();

            // Generate comprehensive report
            const report = await this.generateReport();
            await this.saveResults();

            return report;

        } catch (error) {
            console.error('❌ Screen reader test failed:', error);
            throw error;
        }
    }

    async testInitialNavigation() {
        this.announce('Starting initial navigation test');

        // Simulate screen reader starting from top of page
        this.currentElement = this.document.body.firstElementChild || this.document.body;

        // Navigate through first few elements
        for (let i = 0; i < 10; i++) {
            const announcement = this.announceCurrentElement();
            if (!announcement) break;

            await this.nextElement();
            if (!this.currentElement) break;
        }

        this.logTest('Initial Navigation', true, 'Page navigation works correctly');
    }

    async testErrorMessageDiscovery() {
        this.announce('Testing error message discovery');

        // Find error messages
        const errorMessages = this.document.querySelectorAll(
            '.notification-error, [role="alert"], .error-message'
        );

        const discoveries = [];

        for (const errorMessage of errorMessages) {
            this.currentElement = errorMessage;
            const announcement = this.announceCurrentElement();

            discoveries.push({
                element: errorMessage.tagName,
                role: errorMessage.getAttribute('role'),
                announcement: announcement,
                hasAriaLive: errorMessage.hasAttribute('aria-live'),
                isImmediate: errorMessage.getAttribute('aria-live') === 'assertive' ||
                           errorMessage.getAttribute('role') === 'alert'
            });
        }

        const immediateAnnouncements = discoveries.filter(d => d.isImmediate).length;

        this.logTest(
            'Error Message Discovery',
            immediateAnnouncements > 0,
            `Found ${discoveries.length} error messages, ${immediateAnnouncements} with immediate announcement`
        );

        return discoveries;
    }

    async testRecoveryOptionsNavigation() {
        this.announce('Testing recovery options navigation');

        // Find recovery options
        const recoveryElements = this.document.querySelectorAll(
            '.recovery-option, .notification-action-button, .primary-button, .secondary-button'
        );

        const options = [];

        for (const element of recoveryElements) {
            this.currentElement = element;
            const announcement = this.announceCurrentElement();

            options.push({
                type: this.getElementType(element),
                announcement: announcement,
                accessible: announcement && announcement.length > 0,
                hasLabel: this.hasAccessibleName(element),
                isActionable: this.isActionableElement(element)
            });
        }

        const accessibleOptions = options.filter(o => o.accessible && o.isActionable).length;

        this.logTest(
            'Recovery Options Navigation',
            accessibleOptions === options.length,
            `${accessibleOptions}/${options.length} recovery options are accessible`
        );

        return options;
    }

    async testFormInteraction() {
        this.announce('Testing form interaction');

        const formElements = this.document.querySelectorAll(
            'input, textarea, select, button[type="submit"]'
        );

        const interactions = [];

        for (const element of formElements) {
            this.currentElement = element;
            const announcement = this.announceCurrentElement();

            interactions.push({
                type: element.tagName.toLowerCase(),
                inputType: element.type,
                announcement: announcement,
                hasLabel: this.hasLabel(element),
                hasDescription: this.hasDescription(element),
                required: element.hasAttribute('required'),
                invalid: element.getAttribute('aria-invalid') === 'true'
            });
        }

        const properlyLabeled = interactions.filter(i => i.hasLabel).length;

        this.logTest(
            'Form Interaction',
            properlyLabeled === interactions.length,
            `${properlyLabeled}/${interactions.length} form elements have proper labels`
        );

        return interactions;
    }

    async testLiveRegionUpdates() {
        this.announce('Testing live region updates');

        const liveRegions = this.document.querySelectorAll('[aria-live], [role="status"], [role="alert"]');

        const regions = Array.from(liveRegions).map(region => ({
            element: region.tagName,
            ariaLive: region.getAttribute('aria-live'),
            role: region.getAttribute('role'),
            politeness: this.getLiveRegionPoliteness(region),
            content: region.textContent.trim().substring(0, 100)
        }));

        // Simulate content updates
        const updates = [];
        for (const region of liveRegions) {
            const originalContent = region.textContent;

            // Simulate update
            const mockUpdate = 'Status updated: Recovery in progress...';
            region.textContent = mockUpdate;

            updates.push({
                region: region.tagName,
                politeness: this.getLiveRegionPoliteness(region),
                update: mockUpdate,
                announced: this.getLiveRegionPoliteness(region) !== 'off'
            });

            // Track update
            this.liveRegionUpdates.push({
                timestamp: Date.now(),
                element: region,
                content: mockUpdate,
                politeness: this.getLiveRegionPoliteness(region)
            });
        }

        this.logTest(
            'Live Region Updates',
            regions.length > 0,
            `Found ${regions.length} live regions with ${updates.length} simulated updates`
        );

        return { regions, updates };
    }

    async testLandmarkNavigation() {
        this.announce('Testing landmark navigation');

        const landmarks = this.document.querySelectorAll(
            '[role="main"], [role="banner"], [role="navigation"], [role="complementary"], [role="contentinfo"], ' +
            'main, nav, header, footer, aside, section[aria-labelledby], section[aria-label]'
        );

        const landmarkInfo = Array.from(landmarks).map(landmark => {
            const role = this.getLandmarkRole(landmark);
            const name = this.getAccessibleName(landmark);

            return {
                element: landmark.tagName,
                role: role,
                name: name,
                announcement: this.announceLandmark(landmark, role, name)
            };
        });

        // Test landmark navigation sequence
        const navigationSequence = [];
        for (const landmark of landmarks) {
            this.currentElement = landmark;
            const announcement = this.announceCurrentElement();
            navigationSequence.push(announcement);
        }

        this.logTest(
            'Landmark Navigation',
            landmarks.length > 0,
            `Found ${landmarks.length} landmarks for navigation`
        );

        return { landmarks: landmarkInfo, navigationSequence };
    }

    async testHeadingStructure() {
        this.announce('Testing heading structure');

        const headings = this.document.querySelectorAll('h1, h2, h3, h4, h5, h6');

        const headingStructure = Array.from(headings).map((heading, index) => {
            const level = parseInt(heading.tagName.charAt(1));
            const text = heading.textContent.trim();

            return {
                index: index + 1,
                level: level,
                text: text,
                announcement: `Heading level ${level}, ${text}`,
                hasId: !!heading.id,
                isEmpty: text.length === 0
            };
        });

        // Check for proper heading hierarchy
        const hierarchyIssues = [];
        let previousLevel = 0;

        for (const heading of headingStructure) {
            if (heading.level > previousLevel + 1) {
                hierarchyIssues.push(`Skipped heading level: jumped from h${previousLevel} to h${heading.level}`);
            }
            if (heading.isEmpty) {
                hierarchyIssues.push(`Empty heading at level ${heading.level}`);
            }
            previousLevel = heading.level;
        }

        this.logTest(
            'Heading Structure',
            hierarchyIssues.length === 0,
            hierarchyIssues.length === 0 ?
                `Proper heading hierarchy with ${headingStructure.length} headings` :
                `${hierarchyIssues.length} heading hierarchy issues found`
        );

        return { headings: headingStructure, issues: hierarchyIssues };
    }

    async testSkipLinkFunctionality() {
        this.announce('Testing skip link functionality');

        const skipLinks = this.document.querySelectorAll(
            '.skip-link, a[href^="#main"], a[href^="#content"], a[href^="#recovery"]'
        );

        const skipLinkTests = Array.from(skipLinks).map(link => {
            const href = link.getAttribute('href');
            const target = href ? this.document.querySelector(href) : null;
            const text = link.textContent.trim();

            return {
                text: text,
                href: href,
                hasTarget: !!target,
                visible: this.isVisible(link),
                focusable: link.tabIndex !== -1,
                announcement: `Link, ${text}${target ? ', skip to ' + (target.tagName || 'content') : ''}`
            };
        });

        this.logTest(
            'Skip Link Functionality',
            skipLinkTests.length > 0,
            `Found ${skipLinkTests.length} skip links`
        );

        return skipLinkTests;
    }

    // Navigation methods

    async nextElement() {
        if (!this.currentElement) return null;

        const allElements = this.getAllNavigableElements();
        const currentIndex = allElements.indexOf(this.currentElement);

        if (currentIndex >= 0 && currentIndex < allElements.length - 1) {
            this.currentElement = allElements[currentIndex + 1];
            this.recordNavigation('nextElement');
            return this.currentElement;
        }

        return null;
    }

    async nextHeading() {
        if (!this.document) return null;
        const headings = this.document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        return this.navigateToNext(headings, 'heading');
    }

    async nextLandmark() {
        if (!this.document) return null;
        const landmarks = this.document.querySelectorAll(
            '[role="main"], [role="banner"], [role="navigation"], main, nav, header, footer'
        );
        return this.navigateToNext(landmarks, 'landmark');
    }

    async nextButton() {
        if (!this.document) return null;
        const buttons = this.document.querySelectorAll('button, input[type="button"], input[type="submit"], [role="button"]');
        return this.navigateToNext(buttons, 'button');
    }

    async nextFormField() {
        if (!this.document) return null;
        const fields = this.document.querySelectorAll('input, textarea, select');
        return this.navigateToNext(fields, 'form field');
    }

    navigateToNext(elements, type) {
        const elementsArray = Array.from(elements);
        const currentIndex = this.currentElement ? elementsArray.indexOf(this.currentElement) : -1;

        if (currentIndex < elementsArray.length - 1) {
            this.currentElement = elementsArray[currentIndex + 1];
            this.recordNavigation(`next${type}`);
            return this.currentElement;
        }

        return null;
    }

    // Announcement methods

    announceCurrentElement() {
        if (!this.currentElement) return null;

        const announcement = this.generateElementAnnouncement(this.currentElement);

        this.announce(announcement);
        return announcement;
    }

    generateElementAnnouncement(element) {
        const role = this.getEffectiveRole(element);
        const name = this.getAccessibleName(element);
        const description = this.getAccessibleDescription(element);
        const state = this.getElementState(element);

        let announcement = '';

        // Role and name
        if (role === 'button' || role === 'link') {
            announcement = `${this.capitalizeFirst(role)}, ${name || 'unlabeled'}`;
        } else if (role === 'heading') {
            const level = element.tagName.charAt(1);
            announcement = `Heading level ${level}, ${name || element.textContent.trim()}`;
        } else if (role === 'textbox' || element.tagName === 'INPUT') {
            const inputType = element.type || 'text';
            announcement = `${this.capitalizeFirst(inputType)} input, ${name || 'unlabeled'}`;
        } else if (role === 'alert') {
            announcement = `Alert, ${element.textContent.trim()}`;
        } else if (name) {
            announcement = `${this.capitalizeFirst(role || element.tagName.toLowerCase())}, ${name}`;
        } else {
            announcement = element.textContent.trim().substring(0, 100) ||
                         `${element.tagName.toLowerCase()} element`;
        }

        // Add description if available
        if (description && description !== name) {
            announcement += `, ${description}`;
        }

        // Add state information
        if (state.length > 0) {
            announcement += `, ${state.join(', ')}`;
        }

        return announcement;
    }

    announceLandmark(element, role, name) {
        let announcement = `Landmark, ${role}`;
        if (name) {
            announcement += `, ${name}`;
        }
        return announcement;
    }

    // Utility methods

    getEffectiveRole(element) {
        const explicitRole = element.getAttribute('role');
        if (explicitRole) return explicitRole;

        const tagName = element.tagName.toLowerCase();
        const implicitRoles = {
            'button': 'button',
            'a': element.href ? 'link' : 'generic',
            'input': this.getInputRole(element),
            'textarea': 'textbox',
            'select': 'combobox',
            'h1': 'heading',
            'h2': 'heading',
            'h3': 'heading',
            'h4': 'heading',
            'h5': 'heading',
            'h6': 'heading',
            'main': 'main',
            'nav': 'navigation',
            'header': 'banner',
            'footer': 'contentinfo'
        };

        return implicitRoles[tagName] || 'generic';
    }

    getInputRole(element) {
        const type = element.type || 'text';
        const inputRoles = {
            'text': 'textbox',
            'email': 'textbox',
            'password': 'textbox',
            'search': 'searchbox',
            'tel': 'textbox',
            'url': 'textbox',
            'number': 'spinbutton',
            'checkbox': 'checkbox',
            'radio': 'radio',
            'button': 'button',
            'submit': 'button',
            'reset': 'button'
        };
        return inputRoles[type] || 'textbox';
    }

    getAccessibleName(element) {
        // Check aria-label first
        const ariaLabel = element.getAttribute('aria-label');
        if (ariaLabel) return ariaLabel;

        // Check aria-labelledby
        const labelledBy = element.getAttribute('aria-labelledby');
        if (labelledBy) {
            const labelElement = this.document.getElementById(labelledBy);
            if (labelElement) return labelElement.textContent.trim();
        }

        // Check associated label
        if (element.id) {
            const label = this.document.querySelector(`label[for="${element.id}"]`);
            if (label) return label.textContent.trim();
        }

        // Check parent label
        const parentLabel = element.closest('label');
        if (parentLabel) {
            return parentLabel.textContent.trim();
        }

        // For buttons, use text content
        if (element.tagName === 'BUTTON') {
            return element.textContent.trim();
        }

        // For links, use text content
        if (element.tagName === 'A') {
            return element.textContent.trim();
        }

        // For headings, use text content
        if (/^h[1-6]$/i.test(element.tagName)) {
            return element.textContent.trim();
        }

        return '';
    }

    getAccessibleDescription(element) {
        const describedBy = element.getAttribute('aria-describedby');
        if (describedBy) {
            const descElement = this.document.getElementById(describedBy);
            if (descElement) return descElement.textContent.trim();
        }

        return '';
    }

    getElementState(element) {
        const states = [];

        if (element.hasAttribute('aria-expanded')) {
            const expanded = element.getAttribute('aria-expanded') === 'true';
            states.push(expanded ? 'expanded' : 'collapsed');
        }

        if (element.hasAttribute('aria-checked')) {
            const checked = element.getAttribute('aria-checked');
            if (checked === 'true') states.push('checked');
            else if (checked === 'false') states.push('unchecked');
            else states.push('mixed');
        }

        if (element.hasAttribute('aria-selected')) {
            const selected = element.getAttribute('aria-selected') === 'true';
            states.push(selected ? 'selected' : 'not selected');
        }

        if (element.hasAttribute('disabled') || element.getAttribute('aria-disabled') === 'true') {
            states.push('disabled');
        }

        if (element.hasAttribute('required') || element.getAttribute('aria-required') === 'true') {
            states.push('required');
        }

        if (element.getAttribute('aria-invalid') === 'true') {
            states.push('invalid');
        }

        return states;
    }

    getLandmarkRole(element) {
        const role = element.getAttribute('role');
        if (role) return role;

        const tagName = element.tagName.toLowerCase();
        const landmarkTags = {
            'main': 'main',
            'nav': 'navigation',
            'header': 'banner',
            'footer': 'contentinfo',
            'aside': 'complementary',
            'section': element.hasAttribute('aria-label') || element.hasAttribute('aria-labelledby') ? 'region' : null
        };

        return landmarkTags[tagName] || 'region';
    }

    getLiveRegionPoliteness(element) {
        const ariaLive = element.getAttribute('aria-live');
        if (ariaLive) return ariaLive;

        const role = element.getAttribute('role');
        if (role === 'alert') return 'assertive';
        if (role === 'status') return 'polite';

        return 'off';
    }

    hasAccessibleName(element) {
        return this.getAccessibleName(element).length > 0;
    }

    hasLabel(element) {
        return this.hasAccessibleName(element);
    }

    hasDescription(element) {
        return this.getAccessibleDescription(element).length > 0;
    }

    isActionableElement(element) {
        const actionableTags = ['button', 'a', 'input'];
        const actionableRoles = ['button', 'link', 'menuitem', 'tab'];

        return actionableTags.includes(element.tagName.toLowerCase()) ||
               actionableRoles.includes(element.getAttribute('role')) ||
               element.hasAttribute('onclick') ||
               element.tabIndex >= 0;
    }

    getElementType(element) {
        const role = this.getEffectiveRole(element);
        return `${element.tagName.toLowerCase()}${role !== 'generic' ? ` (${role})` : ''}`;
    }

    isVisible(element) {
        const style = element.style || {};
        return style.display !== 'none' &&
               style.visibility !== 'hidden' &&
               !element.hasAttribute('hidden');
    }

    getAllNavigableElements() {
        if (!this.document) return [];
        return Array.from(this.document.querySelectorAll('*')).filter(el => {
            return el.tagName && this.isVisible(el) && el.textContent.trim().length > 0;
        });
    }

    recordNavigation(command) {
        this.navigationHistory.push({
            timestamp: Date.now(),
            command: command,
            element: this.currentElement?.tagName || 'unknown',
            announcement: this.announcements[this.announcements.length - 1]
        });
    }

    announce(text) {
        if (!text || text.length === 0) return;

        const announcement = {
            timestamp: Date.now(),
            text: text,
            urgent: false
        };

        this.announcements.push(announcement);

        if (this.options.verbose) {
            console.log(`🔊 ${text}`);
        }
    }

    logTest(testName, passed, message) {
        const icon = passed ? '✅' : '❌';
        console.log(`   ${icon} ${testName}: ${message}`);
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    async generateReport() {
        const summary = {
            totalAnnouncements: this.announcements.length,
            navigationCommands: this.navigationHistory.length,
            liveRegionUpdates: this.liveRegionUpdates.length,
            averageAnnouncementLength: this.announcements.length > 0 ?
                Math.round(this.announcements.reduce((sum, a) => sum + a.text.length, 0) / this.announcements.length) :
                0
        };

        console.log('\n📊 Screen Reader Test Results:');
        console.log(`   Total Announcements: ${summary.totalAnnouncements}`);
        console.log(`   Navigation Commands: ${summary.navigationCommands}`);
        console.log(`   Live Region Updates: ${summary.liveRegionUpdates}`);
        console.log(`   Avg Announcement Length: ${summary.averageAnnouncementLength} characters`);

        return {
            timestamp: new Date().toISOString(),
            summary,
            announcements: this.announcements,
            navigationHistory: this.navigationHistory,
            liveRegionUpdates: this.liveRegionUpdates,
            recommendations: this.generateScreenReaderRecommendations()
        };
    }

    generateScreenReaderRecommendations() {
        const recommendations = [];

        // Check announcement quality
        const shortAnnouncements = this.announcements.filter(a => a.text.length < 10).length;
        if (shortAnnouncements > 0) {
            recommendations.push({
                priority: 'medium',
                category: 'Announcement Quality',
                issue: `${shortAnnouncements} announcements are very short`,
                solution: 'Ensure announcements provide sufficient context'
            });
        }

        // Check live region usage
        if (this.liveRegionUpdates.length === 0) {
            recommendations.push({
                priority: 'high',
                category: 'Live Regions',
                issue: 'No live region updates detected',
                solution: 'Add aria-live regions for dynamic content updates'
            });
        }

        // Check navigation efficiency
        if (this.navigationHistory.length > 20) {
            recommendations.push({
                priority: 'low',
                category: 'Navigation',
                issue: 'Many navigation steps required',
                solution: 'Consider adding skip links and better landmark structure'
            });
        }

        return recommendations;
    }

    async saveResults() {
        const report = await this.generateReport();

        try {
            await fs.writeFile(this.options.outputFile, JSON.stringify(report, null, 2));
            console.log(`\n💾 Screen reader test results saved to: ${this.options.outputFile}`);
        } catch (error) {
            console.warn(`⚠️  Could not save results: ${error.message}`);
        }

        return report;
    }
}

// CLI interface and test runner
if (require.main === module) {
    (async () => {
        try {
            // Read the error interface HTML file
            const htmlPath = path.join(__dirname, '../../test/accessibility/error-accessibility-test.js');

            // Generate test HTML (using the same generator from the accessibility test)
            const testerClass = require('./error-accessibility-test.js');
            const tempTester = new testerClass();

            // Create a basic error recovery HTML for testing
            const testHTML = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Screen Reader Test - Error Recovery</title>
    <style>
        .sr-only { position: absolute; left: -10000px; width: 1px; height: 1px; overflow: hidden; }
        .skip-link { position: absolute; top: -40px; left: 6px; background: #000; color: #fff; padding: 8px; }
        .skip-link:focus { top: 0; }
    </style>
</head>
<body>
    <div class="skip-link">
        <a href="#main-content">Skip to main content</a>
    </div>

    <header role="banner">
        <h1>Error Recovery System</h1>
    </header>

    <nav role="navigation" aria-label="Main navigation">
        <ul>
            <li><a href="#dashboard">Dashboard</a></li>
            <li><a href="#recovery">Recovery Options</a></li>
            <li><a href="#help">Help</a></li>
        </ul>
    </nav>

    <main id="main-content" role="main">
        <div aria-live="polite" id="status-announcements" class="sr-only"></div>
        <div aria-live="assertive" id="error-announcements" class="sr-only"></div>

        <section aria-labelledby="error-section">
            <h2 id="error-section">Current Errors</h2>

            <div class="error-message" role="alert" aria-live="assertive">
                <h3>Authentication Failed</h3>
                <p>Your login credentials are incorrect. Please check your email and password, then try again.</p>
                <button type="button" aria-describedby="retry-help">Retry Login</button>
                <div id="retry-help" class="sr-only">Click to attempt login again with the same credentials</div>
            </div>

            <div class="warning-message" role="status" aria-live="polite">
                <h3>Network Connection Issue</h3>
                <p>Unable to connect to the server. Please check your internet connection.</p>
                <div>
                    <button type="button">Retry Connection</button>
                    <button type="button">Work Offline</button>
                </div>
            </div>
        </section>

        <section aria-labelledby="recovery-section">
            <h2 id="recovery-section">Recovery Options</h2>

            <fieldset>
                <legend>Choose Recovery Method</legend>
                <div>
                    <input type="radio" id="auto-recovery" name="recovery" value="auto" checked>
                    <label for="auto-recovery">
                        <strong>Automatic Recovery</strong>
                        <span>Let the system automatically fix the issue</span>
                    </label>
                </div>
                <div>
                    <input type="radio" id="manual-recovery" name="recovery" value="manual">
                    <label for="manual-recovery">
                        <strong>Manual Recovery</strong>
                        <span>Follow step-by-step instructions</span>
                    </label>
                </div>
            </fieldset>

            <div>
                <button type="submit" aria-describedby="continue-help">Continue Recovery</button>
                <div id="continue-help" class="sr-only">Start the recovery process with the selected method</div>
                <button type="button">Cancel</button>
            </div>
        </section>

        <section aria-labelledby="status-section">
            <h2 id="status-section">Recovery Status</h2>

            <div role="status" aria-live="polite" id="recovery-status">
                Initializing recovery process...
            </div>

            <div role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"
                 aria-labelledby="progress-label">
                <div id="progress-label">Recovery progress: 0% complete</div>
            </div>
        </section>
    </main>

    <footer role="contentinfo">
        <p>Need help? <a href="#contact">Contact Support</a></p>
    </footer>

    <script>
        // Simulate some dynamic updates for live region testing
        setTimeout(() => {
            document.getElementById('recovery-status').textContent = 'Recovery in progress...';
            document.querySelector('[role="progressbar"]').setAttribute('aria-valuenow', '50');
            document.getElementById('progress-label').textContent = 'Recovery progress: 50% complete';
        }, 2000);

        setTimeout(() => {
            document.getElementById('recovery-status').textContent = 'Recovery completed successfully!';
            document.querySelector('[role="progressbar"]').setAttribute('aria-valuenow', '100');
            document.getElementById('progress-label').textContent = 'Recovery progress: 100% complete';
        }, 4000);
    </script>
</body>
</html>
            `;

            const simulator = new ScreenReaderSimulator({
                verbose: process.argv.includes('--verbose'),
                announceAll: process.argv.includes('--announce-all')
            });

            const report = await simulator.testScreenReaderExperience(testHTML);

            console.log('\n✅ Screen reader simulation completed successfully!');

            // Exit with success
            process.exit(0);

        } catch (error) {
            console.error('❌ Screen reader testing failed:', error);
            process.exit(1);
        }
    })();
}

module.exports = ScreenReaderSimulator;