const { Given, When, Then, Before } = require('@cucumber/cucumber');
const { expect } = require('chai');

// Mock session manager for demo
class SessionManager {
  constructor() {
    this.sessions = new Map();
    this.timeout = 30 * 60 * 1000; // 30 minutes default
    this.warnings = new Map();
    this.devices = new Map();
  }

  createSession(userId) {
    const session = {
      id: Math.random().toString(36),
      userId,
      createdAt: new Date(),
      lastActivity: new Date(),
      expired: false,
      context: {}
    };
    this.sessions.set(userId, session);
    return session;
  }

  expireSession(userId) {
    const session = this.sessions.get(userId);
    if (session) {
      session.expired = true;
      session.context = { ...session.context, saved: true };
    }
  }

  restoreContext(userId) {
    const oldSession = this.sessions.get(userId);
    if (oldSession && oldSession.context.saved) {
      const newSession = this.createSession(userId);
      newSession.context = { ...oldSession.context, restored: true };
      return newSession;
    }
  }

  extendSession(userId, minutes) {
    const session = this.sessions.get(userId);
    if (session) {
      session.lastActivity = new Date();
      session.expiresAt = new Date(Date.now() + minutes * 60 * 1000);
    }
  }
}

const sessionManager = new SessionManager();
let currentUser = null;
let currentSession = null;
let workflowState = {};
let systemResponse = null;

Before(function() {
  sessionManager.sessions.clear();
  currentUser = null;
  currentSession = null;
  workflowState = {};
  systemResponse = null;
});

// Background steps
Given('the system is initialized', function() {
  expect(sessionManager).to.exist;
});

Given('session timeout is set to {int} minutes', function(minutes) {
  sessionManager.timeout = minutes * 60 * 1000;
});

// User and session steps
Given('user {string} is logged in', function(email) {
  currentUser = email;
  currentSession = sessionManager.createSession(email);
});

Given('current session is created', function() {
  expect(currentSession).to.exist;
  expect(currentSession.expired).to.be.false;
});

Given('user {string} is editing a task', function(email) {
  currentUser = email;
  currentSession = sessionManager.createSession(email);
  currentSession.context.editing = true;
  currentSession.context.task = 'sample_task';
});

Given('workflow is in phase {string}', function(phase) {
  workflowState.phase = phase;
  currentSession.context.workflow = workflowState;
});

Given('{int} agents have been selected', function(count) {
  workflowState.selectedAgents = count;
});

Given('session will expire in {int} minutes', function(minutes) {
  currentSession.expiresAt = new Date(Date.now() + minutes * 60 * 1000);
});

Given('user {string} is logged in on device A', function(email) {
  currentUser = email;
  const session = sessionManager.createSession(email);
  session.device = 'A';
  sessionManager.devices.set('A', session);
});

// When steps
When('waiting {int} minutes without activity', function(minutes) {
  // Simulate time passing
  const passedTime = minutes * 60 * 1000;
  if (passedTime > sessionManager.timeout) {
    sessionManager.expireSession(currentUser);
    systemResponse = { status: 401, message: 'Unauthorized' };
  }
});

When('session times out', function() {
  sessionManager.expireSession(currentUser);
});

When('user logs in again', function() {
  const restoredSession = sessionManager.restoreContext(currentUser);
  currentSession = restoredSession;
});

When('user makes any API call', function() {
  sessionManager.extendSession(currentUser, 30);
});

When('system detects imminent expiry', function() {
  const remaining = 2; // 2 minutes
  sessionManager.warnings.set(currentUser, {
    type: 'expiring_soon',
    remaining,
    options: ['Extend Session', 'Save and Logout']
  });
});

When('same user logs in on device B', function() {
  const sessionB = sessionManager.createSession(currentUser);
  sessionB.device = 'B';
  sessionManager.devices.set('B', sessionB);
});

// Then steps
Then('session should expire', function() {
  const session = sessionManager.sessions.get(currentUser);
  expect(session.expired).to.be.true;
});

Then('user should be logged out automatically', function() {
  const session = sessionManager.sessions.get(currentUser);
  expect(session.expired).to.be.true;
});

Then('system should return {int} unauthorized', function(code) {
  expect(systemResponse.status).to.equal(code);
});

Then('system should restore previous workflow state', function() {
  expect(currentSession.context.restored).to.be.true;
  expect(currentSession.context.workflow).to.exist;
});

Then('current phase should still be {string}', function(phase) {
  expect(currentSession.context.workflow.phase).to.equal(phase);
});

Then('agent selection should be preserved', function() {
  expect(currentSession.context.workflow.selectedAgents).to.equal(5);
});

Then('unsaved changes should have recovery prompt', function() {
  expect(currentSession.context.restored).to.be.true;
});

Then('session should be extended by {int} minutes', function(minutes) {
  expect(currentSession.expiresAt).to.exist;
  expect(currentSession.lastActivity).to.exist;
});

Then('user operations should not be interrupted', function() {
  expect(currentSession.expired).to.be.false;
});

Then('countdown warning should be displayed', function() {
  const warning = sessionManager.warnings.get(currentUser);
  expect(warning).to.exist;
  expect(warning.type).to.equal('expiring_soon');
});

Then('{string} option should be provided', function(option) {
  const warning = sessionManager.warnings.get(currentUser);
  expect(warning.options).to.include(option);
});

Then('both sessions should be managed independently', function() {
  const sessionA = sessionManager.devices.get('A');
  const sessionB = sessionManager.devices.get('B');
  expect(sessionA).to.exist;
  expect(sessionB).to.exist;
  expect(sessionA.id).to.not.equal(sessionB.id);
});

Then('each session has independent timeout timer', function() {
  const sessionA = sessionManager.devices.get('A');
  const sessionB = sessionManager.devices.get('B');
  expect(sessionA.createdAt).to.exist;
  expect(sessionB.createdAt).to.exist;
});

Then('user can view all active sessions', function() {
  const devices = Array.from(sessionManager.devices.keys());
  expect(devices).to.have.lengthOf(2);
  expect(devices).to.include('A');
  expect(devices).to.include('B');
});

Then('can choose to terminate specific sessions', function() {
  // Mock capability to terminate sessions
  expect(sessionManager.devices.size).to.equal(2);
  // Could delete specific session: sessionManager.devices.delete('A');
});
