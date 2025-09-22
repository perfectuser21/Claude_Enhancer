import React, { useState } from 'react';

const QRCodeDisplay = ({ qrCode, manualCode }) => {
  const [showManualCode, setShowManualCode] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopyCode = async () => {
    try {
      await navigator.clipboard.writeText(manualCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy code:', error);
    }
  };

  const formatManualCode = (code) => {
    // Format the code in groups of 4 for better readability
    return code.replace(/(.{4})/g, '$1 ').trim();
  };

  return (
    <div className="qr-code-display">
      <div className="qr-code-container">
        {qrCode ? (
          <img
            src={qrCode}
            alt="QR Code for authenticator app"
            className="qr-code-image"
          />
        ) : (
          <div className="qr-code-placeholder">
            <div className="placeholder-icon">📱</div>
            <p>QR Code loading...</p>
          </div>
        )}
      </div>

      <div className="manual-setup">
        <button
          type="button"
          className="toggle-manual-button"
          onClick={() => setShowManualCode(!showManualCode)}
        >
          {showManualCode ? 'Hide' : 'Show'} manual setup code
        </button>

        {showManualCode && manualCode && (
          <div className="manual-code-section">
            <p className="manual-instructions">
              If you can't scan the QR code, enter this code manually in your authenticator app:
            </p>

            <div className="manual-code-container">
              <code className="manual-code">
                {formatManualCode(manualCode)}
              </code>

              <button
                type="button"
                className="copy-button"
                onClick={handleCopyCode}
                title="Copy to clipboard"
              >
                {copied ? (
                  <>
                    <span className="copy-icon">✓</span>
                    Copied!
                  </>
                ) : (
                  <>
                    <span className="copy-icon">📋</span>
                    Copy
                  </>
                )}
              </button>
            </div>

            <div className="setup-notes">
              <h4>Setup Instructions:</h4>
              <ol>
                <li>Open your authenticator app</li>
                <li>Select "Add account" or "+" button</li>
                <li>Choose "Enter setup key manually"</li>
                <li>Enter the code above</li>
                <li>Set account name to "Perfect21" or your preference</li>
              </ol>
            </div>
          </div>
        )}
      </div>

      <div className="qr-help">
        <h4>Recommended Authenticator Apps:</h4>
        <ul className="app-recommendations">
          <li>
            <strong>Google Authenticator</strong> - Simple and reliable
          </li>
          <li>
            <strong>Authy</strong> - Multi-device sync and backup
          </li>
          <li>
            <strong>Microsoft Authenticator</strong> - Push notifications
          </li>
          <li>
            <strong>1Password</strong> - Integrated password manager
          </li>
        </ul>
      </div>
    </div>
  );
};

export default QRCodeDisplay;