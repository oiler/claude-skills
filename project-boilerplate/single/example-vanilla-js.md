# CSV Data Converter

Convert CSV files to multiple formats with client-side processing and data validation.

---

## Basic Information

**Project:** CSV Data Converter  
**Type:** ☑ Vanilla JS App  
**Purpose:** Convert CSV files to JSON, XML, and SQL formats with validation and preview  
**Status:** ☑ Active Development

---

## Tech Stack

**Primary:**
- Vanilla JavaScript (ES6+)
- HTML5
- CSS3 / Sass (dart-sass)

**Build Tools:**
- dart-sass for CSS compilation
- No bundler (vanilla JS with ES6 modules)

**Runtime:**
- Browser-based (no server required)
- File API for client-side file processing

**Browser Support:**
- Chrome/Edge >= 90, Firefox >= 88, Safari >= 14 (features from 2017+)

---

## Code Standards

### JavaScript
- Functional patterns over classes
- ES6+ features: arrow functions, destructuring, template literals, modules
- No polyfills (target modern browsers only)
- Modular code: one module per feature
- Pure functions where possible
- Meaningful variable names over brevity

### HTML
- Semantic HTML5 elements
- Accessible forms with proper labels
- ARIA attributes where needed
- No inline JavaScript

### CSS/Sass
- Semantic class names (BEM methodology)
- Three-folder structure: vendor/, core/, pages/
- Maximum 2-3 levels of nesting
- CSS custom properties for theming
- Mobile-first responsive design
- Compile: `sass --watch src/css:dist/css --style compressed`

### Git
- Atomic commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
- Interactive rebase for clean history
- Force push with `--force-with-lease` only

---

## Project Structure

```
csv-converter/
├── src/
│   ├── js/
│   │   ├── main.js              # Entry point, app initialization
│   │   ├── modules/
│   │   │   ├── csv-parser.js    # CSV parsing logic
│   │   │   ├── converter.js     # Format conversion
│   │   │   ├── validator.js     # Data validation
│   │   │   └── ui-controller.js # UI updates and events
│   │   └── utils/
│   │       ├── file-handler.js  # File reading utilities
│   │       ├── download.js      # File download helper
│   │       └── string-utils.js  # String manipulation
│   ├── css/
│   │   ├── vendor/              # Third-party CSS (if any)
│   │   ├── core/
│   │   │   ├── _variables.scss  # Colors, spacing, etc.
│   │   │   ├── _mixins.scss     # Reusable mixins
│   │   │   ├── _reset.scss      # CSS reset
│   │   │   └── _typography.scss # Font styles
│   │   ├── pages/
│   │   │   ├── _converter.scss  # Main converter page
│   │   │   └── _preview.scss    # Preview panel
│   │   └── main.scss            # Import all partials
│   └── index.html               # Main HTML file
├── dist/                        # Build output
│   ├── css/
│   │   └── main.css
│   └── js/                      # (if using bundler later)
├── tests/
│   ├── unit/
│   │   ├── csv-parser.test.js
│   │   ├── validator.test.js
│   │   └── converter.test.js
│   └── fixtures/
│       └── sample-data.csv
└── README.md
```

---

## Key Patterns & Conventions

### Module Pattern
```javascript
// modules/csv-parser.js
export function parseCSV(csvString) {
  const lines = csvString.trim().split('\n');
  const headers = lines[0].split(',').map(h => h.trim());
  
  return lines.slice(1).map(line => {
    const values = line.split(',');
    return headers.reduce((obj, header, index) => {
      obj[header] = values[index]?.trim() || '';
      return obj;
    }, {});
  });
}

export function validateCSVStructure(csvString) {
  // Validation logic
  return { valid: true, errors: [] };
}
```

### Pure Functions for Data Transformation
```javascript
// modules/converter.js
export const toJSON = (data) => {
  return JSON.stringify(data, null, 2);
};

export const toXML = (data) => {
  const rows = data.map(obj => {
    const fields = Object.entries(obj)
      .map(([key, value]) => `    <${key}>${escapeXML(value)}</${key}>`)
      .join('\n');
    return `  <row>\n${fields}\n  </row>`;
  }).join('\n');
  
  return `<?xml version="1.0" encoding="UTF-8"?>\n<data>\n${rows}\n</data>`;
};

const escapeXML = (str) => {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
};
```

### Event Handling
```javascript
// modules/ui-controller.js
export function initializeApp() {
  const fileInput = document.getElementById('csv-file');
  const convertBtn = document.getElementById('convert-btn');
  
  fileInput.addEventListener('change', handleFileSelect);
  convertBtn.addEventListener('click', handleConversion);
}

const handleFileSelect = async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  
  try {
    const content = await readFile(file);
    displayPreview(content);
  } catch (error) {
    showError(`Error reading file: ${error.message}`);
  }
};
```

---

## Testing Requirements

**Priority Areas:**
1. CSV parsing with various edge cases (malformed data, empty fields)
2. Data validation logic (security critical)
3. Format conversion accuracy

**Test Types Enabled:**
- ☑ Unit tests (target: 85%)
- ☑ Integration tests (file handling flow)
- ☑ Security tests (XSS prevention in outputs)

**Critical Test Scenarios:**
1. Parse CSV with quoted fields containing commas
2. Handle empty cells and missing data
3. Validate large files (>1MB) without freezing UI
4. Prevent XSS in XML/SQL output generation
5. Handle UTF-8 and special characters correctly
6. Test with malformed CSV (different column counts per row)

---

## Development Commands

```bash
# Watch and compile Sass
sass --watch src/css:dist/css --style compressed

# Run tests (using Jest or Vitest)
npm test

# Run tests in watch mode
npm run test:watch

# Serve locally (using simple HTTP server)
npx serve .
```

---

## Environment Setup

**Required:**
- Modern browser (Chrome/Firefox/Safari/Edge)
- Node.js (for build tools only, not runtime)
- dart-sass via Homebrew

**Installation:**
```bash
# Install dart-sass
brew install sass/sass/sass

# Install dev dependencies
npm install
```

---

## Security Checklist

- ☑ Sanitize CSV input before parsing
- ☑ Escape output for XML generation (prevent XXE)
- ☑ Escape output for SQL generation (prevent injection)
- ☑ Validate file size before processing (prevent DoS)
- ☑ No eval() or Function() constructors
- ☑ CSP headers set (if served from server)
- ☑ HTTPS only in production

---

## Common Gotchas

**Issue:** CSV parsing fails on quoted fields with commas
- Solution: Use proper CSV parser that handles RFC 4180 quoted fields, or implement quote-aware splitting

**Issue:** Large files freeze the browser
- Solution: Process CSV in chunks using async/await with setTimeout for yielding to UI thread

**Issue:** Downloaded files have incorrect line endings
- Solution: Use `\r\n` for Windows compatibility in generated files

**Issue:** Special characters (émojis, accents) display incorrectly
- Solution: Ensure UTF-8 encoding throughout, use `new TextEncoder().encode()` for downloads

---

## Claude Instructions

### Skills to Use
- ☑ css-specialist (for Sass architecture)
- ☑ web-security (for output sanitization)

### Testing Approach
- Write tests for: All parsing and conversion functions, validation logic
- Test automatically: Every new utility function, all edge cases
- Skip testing: Simple UI update functions, event listeners

### Code Generation Preferences
- Comment level: ☑ Only complex logic
- Explanation style: ☑ Brief
- Pattern to follow: Functional programming, pure functions, modular code

---

## Quick Reference

### Key Files
- `src/js/main.js` - App initialization and event binding
- `src/js/modules/csv-parser.js` - Core parsing logic
- `src/js/modules/converter.js` - Format conversion functions
- `src/js/modules/validator.js` - Data validation
- `src/css/main.scss` - Main Sass entry point

### External Resources
- [File API MDN](https://developer.mozilla.org/en-US/docs/Web/API/File_API)
- [CSV RFC 4180](https://datatracker.ietf.org/doc/html/rfc4180)
- [ES6 Modules](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)

### Text Domain / Namespace
- None (vanilla JS, no framework)
- Module exports for all functions

---

## Notes & Decisions

**2026-01-19**: Using native ES6 modules (type="module") instead of bundler. Decided to keep it simple for small project size and avoid build complexity.

**2026-01-19**: Processing files entirely client-side for privacy - no data sent to server. This limits file size to ~50MB to prevent browser freezing.

**2026-01-19**: Implemented chunk processing for large files: parse CSV in 1000-row batches with async/await to keep UI responsive.

**2026-01-19**: Using PapaParse library for robust CSV parsing (handles quoted fields, different delimiters, etc.). Imported as ES module from CDN.
