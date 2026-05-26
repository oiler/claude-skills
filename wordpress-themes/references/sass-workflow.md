# Sass Workflow

dart-sass via Homebrew for compiling a classic WordPress theme's SCSS. Watch mode for development, compressed builds for production, plus a helper function for per-page stylesheets.

## Setup (dart-sass via Homebrew)

```bash
# Installation
brew install sass/sass/sass
brew upgrade sass

# Watch mode (development)
cd src/scss
sass styles.scss:../../assets/css/styles.css --watch

# Build mode (production)
sass styles.scss:../../assets/css/styles.css --style=compressed
```

## Helpful Shell Aliases (zsh)

```bash
alias sassw='sass styles.scss:../../assets/css/styles.css --watch'
alias sassb='sass styles.scss:../../assets/css/styles.css --style=compressed'

# Page-specific Sass compilation
sassp() {
  if [[ -z "$1" ]]; then
    echo "Usage: sassp <filename> [build]"
    return 1
  fi
  if [[ "$2" == "build" ]]; then
    sass pages/${1}.scss:../../assets/css/pages/${1}.css --style=compressed
  else
    sass pages/${1}.scss:../../assets/css/pages/${1}.css --watch
  fi
}
```
