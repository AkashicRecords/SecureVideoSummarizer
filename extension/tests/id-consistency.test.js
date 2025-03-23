/**
 * Element ID Consistency Tests
 * 
 * Verifies that all HTML elements referenced in JavaScript have matching IDs in HTML.
 * Particularly focuses on elements needed for both YouTube and Olympus functionality.
 */

const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

describe('Element ID Consistency', () => {
  let htmlContent;
  let popupHtmlContent;
  let jsContent;
  
  beforeAll(() => {
    // Read the main HTML and JS files
    htmlContent = fs.readFileSync(path.resolve(__dirname, '../popup.html'), 'utf8');
    popupJsContent = fs.readFileSync(path.resolve(__dirname, '../popup.js'), 'utf8');
    contentJsContent = fs.readFileSync(path.resolve(__dirname, '../content.js'), 'utf8');
    
    // Optional - read CSS if needed
    try {
      cssContent = fs.readFileSync(path.resolve(__dirname, '../popup.css'), 'utf8');
    } catch (e) {
      cssContent = '';
    }
  });
  
  test('All DOM elements from popup.js exist in popup.html', () => {
    // Parse the HTML
    const dom = new JSDOM(htmlContent);
    const document = dom.window.document;
    
    // Extract getElementById calls from JS
    const getElementByIdRegex = /getElementById\(['"]([^'"]+)['"]\)/g;
    const querySelectorRegex = /querySelector\(['"]#([^'"]+)['"]\)/g;
    
    const jsElementIds = new Set();
    let match;
    
    // Match getElementById
    while ((match = getElementByIdRegex.exec(popupJsContent)) !== null) {
      jsElementIds.add(match[1]);
    }
    
    // Match querySelector with ID
    while ((match = querySelectorRegex.exec(popupJsContent)) !== null) {
      jsElementIds.add(match[1]);
    }
    
    // Check each ID exists in HTML
    const missingIds = [];
    jsElementIds.forEach(id => {
      const element = document.getElementById(id);
      if (!element) {
        missingIds.push(id);
      }
    });
    
    // Output helpful message on failure
    if (missingIds.length > 0) {
      console.error('Missing HTML elements referenced in popup.js:', missingIds);
    }
    
    expect(missingIds).toHaveLength(0);
  });
  
  test('Platform-specific UI elements exist for both YouTube and Olympus', () => {
    // Parse the HTML
    const dom = new JSDOM(htmlContent);
    const document = dom.window.document;
    
    // List of elements that should exist for platform support
    const platformElements = [
      'platform-specific-section',
      'platform-icon',
      'platform-name',
      'youtube-options',
      'olympus-options',
      'olympus-api-status',
      'olympus-features',
      'capture-olympus-transcript'
    ];
    
    // Check each required element exists
    const missingElements = [];
    platformElements.forEach(id => {
      const element = document.getElementById(id);
      if (!element) {
        missingElements.push(id);
      }
    });
    
    // Output helpful message on failure
    if (missingElements.length > 0) {
      console.error('Missing platform-specific UI elements:', missingElements);
    }
    
    expect(missingElements).toHaveLength(0);
  });
  
  test('YouTube and Olympus functions are properly referenced in content.js', () => {
    // Required function names that should exist in content.js
    const requiredFunctions = [
      'findMainVideoElement',
      'extractYouTubeVideoMetadata',
      'findOlympusPlayer',
      'extractOlympusVideoMetadata',
      'detectPlatform'
    ];
    
    const missingFunctions = [];
    
    requiredFunctions.forEach(funcName => {
      const pattern = new RegExp(`function\\s+${funcName}\\s*\\(|const\\s+${funcName}\\s*=\\s*function|let\\s+${funcName}\\s*=\\s*function`);
      if (!pattern.test(contentJsContent)) {
        missingFunctions.push(funcName);
      }
    });
    
    // Output helpful message on failure
    if (missingFunctions.length > 0) {
      console.error('Missing required functions in content.js:', missingFunctions);
    }
    
    expect(missingFunctions).toHaveLength(0);
  });
  
  test('Popup.js has handlers for both YouTube and Olympus buttons', () => {
    // Check for event listeners for platform buttons
    const youtubeButtonRegex = /getElementById\(['"]youtube-summarize-btn['"].*addEventListener/s;
    const olympusButtonRegex = /getElementById\(['"]capture-olympus-transcript['"].*addEventListener/s;
    
    expect(youtubeButtonRegex.test(popupJsContent)).toBe(true);
    expect(olympusButtonRegex.test(popupJsContent)).toBe(true);
  });
}); 