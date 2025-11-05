# Build Setup Reference

## Installation

### dart-sass via Homebrew
```bash
brew install sass/sass/sass
```

Verify installation:
```bash
sass --version
```

## zsh Configuration

Add these aliases to `~/.zshrc`:

```bash
# Main stylesheet builds
alias sassbuild='sass styles.scss:dist/styles.css --style=compressed'
alias sassw='sass styles.scss:dist/styles.css --watch'

# Page-specific builds
sasspage() {
    if [[ -z "$1" ]]; then
        echo "Usage: sasspage <filename> (without .scss extension)"
        return 1
    fi
    sass pages/${1}.scss:dist/pages/${1}.css --style=compressed
}

sasspagew() {
    if [[ -z "$1" ]]; then
        echo "Usage: sasspagew <filename> (without .scss extension)" 
        return 1
    fi
    sass pages/${1}.scss:dist/pages/${1}.css --watch
}
```

After editing `.zshrc`, reload with:
```bash
source ~/.zshrc
```

## Usage

### Main Stylesheet
```bash
# Production build (minified)
sassbuild

# Development build with watch mode (unminified)
sassw
```

### Page-Specific Stylesheets
```bash
# Production build for single.scss
sasspage single

# Development build with watch mode for guides.scss
sasspagew guides
```

## Project Structure

```
project-root/
├── vendor/
│   └── reset.css
├── core/
│   ├── vars.scss
│   ├── utils.scss
│   └── mixins.scss
├── pages/
│   ├── single.scss
│   ├── guides.scss
│   └── post.scss
├── styles.scss          # Main entry point
└── dist/
    ├── styles.css       # Compiled main stylesheet
    └── pages/
        ├── single.css
        ├── guides.css
        └── post.css
```

## Build Flags

- `--style=compressed` - Minifies output for production
- `--watch` - Automatically recompiles on file changes
- `--source-map` - Generates source maps (optional)
- `--no-source-map` - Disables source maps (optional)

## Common Workflows

### Starting Development
```bash
# Terminal 1: Watch main stylesheet
sassw

# Terminal 2: Watch specific page (if needed)
sasspagew single
```

### Production Build
```bash
# Build everything for production
sassbuild
sasspage single
sasspage guides
sasspage post
```

### Tips
- Use watch mode during development for instant feedback
- Run production builds before committing to ensure minification works
- Keep separate terminals for different watch processes
- The `--watch` flag catches changes in imported files (@use, @import)