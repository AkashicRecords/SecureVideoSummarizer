#!/usr/bin/env node

/**
 * Extension Packaging Script
 * 
 * Creates a ZIP file of the extension for distribution
 */

const fs = require('fs');
const path = require('path');
const archiver = require('archiver');
const chalk = require('chalk');
const { version } = require('../package.json');

// Paths
const DIST_DIR = path.resolve(__dirname, '../dist');
const OUTPUT_DIR = path.resolve(__dirname, '../release');
const OUTPUT_FILE = path.join(OUTPUT_DIR, `secure-video-summarizer-v${version}.zip`);

// Make sure the release directory exists
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// Create a file to stream archive data to
const output = fs.createWriteStream(OUTPUT_FILE);
const archive = archiver('zip', {
  zlib: { level: 9 } // Best compression
});

// Listen for all archive data to be written
output.on('close', function() {
  const sizeMB = (archive.pointer() / 1024 / 1024).toFixed(2);
  console.log(chalk.green(`✅ Extension packaged successfully!`));
  console.log(chalk.blue(`📦 Package size: ${sizeMB} MB`));
  console.log(chalk.blue(`📄 File: ${OUTPUT_FILE}`));
});

// Handle warnings
archive.on('warning', function(err) {
  if (err.code === 'ENOENT') {
    console.warn(chalk.yellow(`⚠️  Warning: ${err}`));
  } else {
    throw err;
  }
});

// Handle errors
archive.on('error', function(err) {
  console.error(chalk.red(`❌ Error creating archive: ${err}`));
  process.exit(1);
});

// Pipe archive data to the file
archive.pipe(output);

// Check if dist directory exists
if (!fs.existsSync(DIST_DIR)) {
  console.error(chalk.red(`❌ Distribution directory not found: ${DIST_DIR}`));
  console.error(chalk.yellow(`   Run 'npm run build' first to generate the distribution files.`));
  process.exit(1);
}

// Verify manifest exists
const manifestPath = path.join(DIST_DIR, 'manifest.json');
if (!fs.existsSync(manifestPath)) {
  console.error(chalk.red(`❌ manifest.json not found in ${DIST_DIR}`));
  process.exit(1);
}

// Read manifest to verify version
try {
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  if (manifest.version !== version) {
    console.warn(chalk.yellow(`⚠️  Warning: Package.json version (${version}) doesn't match manifest.json version (${manifest.version})`));
  }
} catch (error) {
  console.error(chalk.red(`❌ Error reading manifest.json: ${error}`));
}

console.log(chalk.blue(`📦 Creating extension package v${version}...`));

// Add all files from dist directory
archive.directory(DIST_DIR, false);

// Finalize the archive
archive.finalize(); 