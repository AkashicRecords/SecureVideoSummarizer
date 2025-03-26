# Naming Conventions

## Current Inconsistencies

### Platform-Related Elements
Current mixed usage:
- `platform-specific-section`
- `platform-info`
- `platform-icon`
- `platform-name`
- `platform-options`
- `platform-badge`

### Button Elements
Current mixed usage:
- `retry-connection`
- `refresh-content-script`
- `youtube-summarize-btn`
- `action-button`

### Status Elements
Current mixed usage:
- `loading`
- `extension-error`
- `status-message`
- `status-container`

## Proposed Standardization

### 1. Platform Elements
All platform-related elements should use the `platform-` prefix:
```html
<!-- Before -->
<div id="platform-specific-section">
<div class="platform-info">
<img id="platform-icon">

<!-- After -->
<div id="platform-section">
<div class="platform-info">
<img id="platform-icon">
```

### 2. Button Elements
All buttons should use the `btn-` prefix:
```html
<!-- Before -->
<button id="retry-connection">
<button id="refresh-content-script">
<button id="youtube-summarize-btn">

<!-- After -->
<button id="btn-retry">
<button id="btn-refresh">
<button id="btn-summarize-youtube">
```

### 3. Status Elements
All status-related elements should use the `status-` prefix:
```html
<!-- Before -->
<div id="loading">
<div id="extension-error">
<div class="status-message">

<!-- After -->
<div id="status-loading">
<div id="status-error">
<div class="status-message">
```

### 4. Container Elements
All container elements should use the `container-` prefix:
```html
<!-- Before -->
<div id="popup-container">
<div id="summary-container">

<!-- After -->
<div id="container-popup">
<div id="container-summary">
```

### 5. Form Elements
All form elements should use the `form-` prefix:
```html
<!-- Before -->
<select id="summary-length">
<select id="format">
<input id="focus-key-points">

<!-- After -->
<select id="form-length">
<select id="form-format">
<input id="form-focus-key">
```

### 6. Content Elements
All content elements should use the `content-` prefix:
```html
<!-- Before -->
<div id="video-title">
<div id="video-duration">
<div id="summary-content">

<!-- After -->
<div id="content-title">
<div id="content-duration">
<div id="content-summary">
```

## Implementation Plan

### Phase 1: HTML Updates
1. Update all element IDs in `popup.html`
2. Update all element references in JavaScript
3. Update all element references in CSS

### Phase 2: CSS Updates
1. Update all class names in `popup.css`
2. Update all selectors to match new naming convention
3. Update all style references

### Phase 3: JavaScript Updates
1. Update all element selectors in `popup.js`
2. Update all event listeners
3. Update all DOM manipulation code

### Phase 4: Testing
1. Test all UI interactions
2. Verify all styles are applied correctly
3. Check for any broken functionality

## Benefits
1. Improved code readability
2. Easier maintenance
3. Consistent pattern recognition
4. Better organization
5. Reduced naming conflicts

## Migration Strategy
1. Create new elements with new naming convention
2. Keep old elements temporarily
3. Gradually migrate functionality
4. Remove old elements once migration is complete
5. Update documentation

## Example of Complete Migration

### Before
```html
<div id="popup-container">
  <div id="platform-specific-section">
    <div class="platform-info">
      <button id="youtube-summarize-btn" class="action-button">
        <div id="loading" class="status-message">
          <select id="summary-length">
```

### After
```html
<div id="container-popup">
  <div id="platform-section">
    <div class="platform-info">
      <button id="btn-summarize-youtube" class="btn-primary">
        <div id="status-loading" class="status-message">
          <select id="form-length">
``` 