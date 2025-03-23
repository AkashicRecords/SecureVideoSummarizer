#!/usr/bin/env node

/**
 * Element ID Validation Script
 * 
 * This script scans HTML, CSS, and JavaScript files to ensure element IDs 
 * are consistently referenced across the codebase.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Config
const EXTENSION_ROOT = path.resolve(__dirname, '..');
const DIRS_TO_SCAN = [
  '', // Root directory
  'tests'
];
const IGNORE_DIRS = [
  'node_modules',
  'coverage',
  'dist',
  '.git'
];

// Store all the IDs we find
const htmlIds = new Set();
const cssSelectors = new Set();
const jsReferences = new Set();

// Track ID mismatches
const mismatches = [];

// Helper for reading files
function readFilesInDir(dir, filePattern, processor) {
  const fullDir = path.join(EXTENSION_ROOT, dir);
  if (!fs.existsSync(fullDir)) return;
  
  try {
    const files = fs.readdirSync(fullDir).filter(file => 
      !IGNORE_DIRS.includes(file) && 
      filePattern.test(file) && 
      fs.statSync(path.join(fullDir, file)).isFile()
    );
    
    for (const file of files) {
      const filePath = path.join(fullDir, file);
      const content = fs.readFileSync(filePath, 'utf8');
      processor(content, filePath);
    }
  } catch (err) {
    console.error(`Error reading directory ${fullDir}:`, err);
  }
}

// Extract IDs from HTML files
function extractHtmlIds(content, filePath) {
  console.log(`Scanning HTML file: ${path.relative(EXTENSION_ROOT, filePath)}`);
  
  // Match id="something" or id='something'
  const idRegex = /id=["']([^"']+)["']/g;
  let match;
  
  while ((match = idRegex.exec(content)) !== null) {
    htmlIds.add(match[1]);
  }
}

// Extract ID selectors from CSS
function extractCssSelectors(content, filePath) {
  console.log(`Scanning CSS file: ${path.relative(EXTENSION_ROOT, filePath)}`);
  
  // Match #id { ... } pattern
  const idSelectorRegex = /#([a-zA-Z][\w-]*)\b/g;
  let match;
  
  while ((match = idSelectorRegex.exec(content)) !== null) {
    cssSelectors.add(match[1]);
  }
}

// Extract ID references from JavaScript
function extractJsReferences(content, filePath) {
  console.log(`Scanning JS file: ${path.relative(EXTENSION_ROOT, filePath)}`);
  
  // Match getElementById('something') pattern
  const getElementByIdRegex = /getElementById\(["']([^"']+)["']\)/g;
  let match;
  
  while ((match = getElementByIdRegex.exec(content)) !== null) {
    jsReferences.add(match[1]);
  }
  
  // Match document.querySelector('#something') pattern
  const querySelectorRegex = /querySelector\(["']#([^"']+)["']\)/g;
  while ((match = querySelectorRegex.exec(content)) !== null) {
    jsReferences.add(match[1]);
  }
  
  // Match document.querySelectorAll('#something') pattern
  const querySelectorAllRegex = /querySelectorAll\(["']#([^"']+)["']\)/g;
  while ((match = querySelectorAllRegex.exec(content)) !== null) {
    jsReferences.add(match[1]);
  }
}

// Scan the codebase
function scanCodebase() {
  console.log('Starting scan of extension codebase...');
  
  // Process each directory
  for (const dir of DIRS_TO_SCAN) {
    // HTML files
    readFilesInDir(dir, /\.html$/i, extractHtmlIds);
    
    // CSS files
    readFilesInDir(dir, /\.css$/i, extractCssSelectors);
    
    // JavaScript files
    readFilesInDir(dir, /\.js$/i, extractJsReferences);
  }
  
  console.log('\nScan complete! Analyzing results...');
}

// Analyze results for potential issues
function analyzeResults() {
  console.log('\n--- ELEMENT ID ANALYSIS ---');
  
  // Check for CSS selectors without corresponding HTML IDs
  for (const cssId of cssSelectors) {
    if (!htmlIds.has(cssId)) {
      mismatches.push({
        type: 'CSS selector without HTML element',
        id: cssId
      });
    }
  }
  
  // Check for JS references without corresponding HTML IDs
  for (const jsId of jsReferences) {
    if (!htmlIds.has(jsId)) {
      mismatches.push({
        type: 'JavaScript reference without HTML element',
        id: jsId
      });
    }
  }
  
  // Print statistics
  console.log(`HTML IDs found: ${htmlIds.size}`);
  console.log(`CSS selectors found: ${cssSelectors.size}`);
  console.log(`JavaScript references found: ${jsReferences.size}`);
  
  // Report on mismatches
  if (mismatches.length > 0) {
    console.log('\n--- POTENTIAL ID MISMATCHES ---');
    for (const issue of mismatches) {
      console.log(`- ${issue.type}: #${issue.id}`);
    }
    console.log(`\nFound ${mismatches.length} potential ID mismatches.`);
    return false;
  } else {
    console.log('\n✅ No ID mismatches found! All elements are correctly referenced.');
    return true;
  }
}

// Run the validation
function validate() {
  scanCodebase();
  return analyzeResults();
}

// When run directly
if (require.main === module) {
  const success = validate();
  process.exit(success ? 0 : 1);
}

module.exports = { validate }; 