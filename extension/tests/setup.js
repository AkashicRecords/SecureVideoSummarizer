// Jest test setup file
const { TextEncoder, TextDecoder } = require('util');

// Add TextEncoder and TextDecoder to global
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder; 