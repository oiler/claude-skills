# CSS Specialist Skill - Installation Guide

## What You've Created

A Claude Skill that provides expert CSS guidance tailored to your specific needs:
- Modern CSS features (2020-2025) with widespread browser support
- Advanced animations and visual effects
- Respects your clean, semantic coding style
- Understands your Sass/dart-sass build pipeline
- References your project structure and workflow

## Files to Download

You'll need to save these 4 artifacts as separate files:

### 1. SKILL.md (Main skill file)
The core skill file with metadata and instructions for Claude.

### 2. resources/build-setup.md
Reference for your zsh aliases and build pipeline configuration.

### 3. resources/modern-features.md
Comprehensive guide to modern CSS features with browser support and examples.

### 4. This guide
Installation instructions.

## Installation Steps

### For Claude.ai (Desktop/Web App)

1. **Enable Skills** (if not already enabled)
   - Go to Settings
   - Navigate to the Skills section
   - Enable Skills feature
   - (Team/Enterprise users: Admin must enable org-wide first)

2. **Create the skill folder structure**
   ```bash
   mkdir -p css-specialist/resources
   ```

3. **Save the files**
   - Save `SKILL.md` to `css-specialist/SKILL.md`
   - Save `build-setup.md` to `css-specialist/resources/build-setup.md`
   - Save `modern-features.md` to `css-specialist/resources/modern-features.md`

4. **Upload to Claude**
   - In Claude.ai, use the skill creator or manual upload
   - Upload the entire `css-specialist` folder
   - Claude will automatically detect when to use it

### For Claude Code

1. **Create the skill directory**
   ```bash
   # For personal use across all projects
   mkdir -p ~/.claude/skills/css-specialist/resources
   
   # OR for project-specific use
   mkdir -p .claude/skills/css-specialist/resources
   ```

2. **Save the files**
   ```bash
   # Personal installation
   # Save SKILL.md to ~/.claude/skills/css-specialist/SKILL.md
   # Save resources to ~/.claude/skills/css-specialist/resources/
   
   # OR Project installation  
   # Save SKILL.md to .claude/skills/css-specialist/SKILL.md
   # Save resources to .claude/skills/css-specialist/resources/
   ```

3. **Restart Claude Code**
   - Skills load at startup
   - Restart to activate the new skill

4. **Verify installation**
   ```bash
   # List installed skills
   ls ~/.claude/skills/
   
   # View the skill
   cat ~/.claude/skills/css-specialist/SKILL.md
   ```

### For Claude API

1. **Create skill folder** as shown above

2. **Reference in API calls**
   - Use the `/v1/skills` endpoint
   - See [Skills API documentation](https://docs.anthropic.com/en/api/messages-examples#skills)

## How to Use

Once installed, simply ask CSS-related questions naturally:

- "How can I use container queries in my card component?"
- "What's the modern way to handle responsive typography?"
- "Help me animate this element with better performance"
- "Show me how to use CSS nesting with my Sass setup"

Claude will **automatically invoke this skill** when it detects CSS-related questions. You'll see it referenced in Claude's thinking process.

## Testing Your Skill

Try these test queries to ensure it's working:

1. **Basic test:**
   ```
   What modern CSS features should I know about?
   ```
   
2. **Build-specific test:**
   ```
   How do I compile my page stylesheets for production?
   ```

3. **Style-specific test:**
   ```
   Show me how to use container queries with semantic class names
   ```

If Claude doesn't reference the skill, check:
- YAML frontmatter is properly formatted (name and description fields)
- File is named exactly `SKILL.md` (case-sensitive)
- Skill folder is in the correct location
- Claude has been restarted (for Claude Code)

## Updating the Skill

To update or modify:

1. **Edit the files** in place
2. **For Claude Code:** Restart to load changes
3. **For Claude.ai:** Re-upload the modified folder
4. **Version tracking:** Update the version number in SKILL.md frontmatter

## Sharing the Skill

To share with team members:

1. **Package the folder:**
   ```bash
   zip -r css-specialist.zip css-specialist/
   ```

2. **Share via:**
   - Version control (git)
   - Cloud storage
   - Direct file transfer

3. **Recipients follow installation steps** for their environment

## Troubleshooting

**Skill not loading?**
- Verify file structure matches exactly
- Check YAML frontmatter formatting
- Ensure no typos in `SKILL.md` filename

**Claude not using skill?**
- Make description more specific to your use case
- Try more explicit questions that match the description
- Check that Skills are enabled in settings

**Resources not loading?**
- Verify `resources/` folder structure
- Ensure markdown files are properly formatted
- Check that SKILL.md references resources correctly

## Additional Resources

- [Claude Skills Documentation](https://docs.claude.com/en/docs/claude-code/skills)
- [Anthropic Skills Repository](https://github.com/anthropics/skills)
- [Skills Engineering Blog](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

## What Makes This Skill Special

Unlike generic CSS help, this skill:
- Knows your exact build setup and aliases
- Respects your coding style preferences
- Focuses on modern features with good browser support
- Understands your project structure
- Provides examples that fit your workflow
- References your specific pain points (modern CSS, animations)

Enjoy your personalized CSS specialist! 🎨