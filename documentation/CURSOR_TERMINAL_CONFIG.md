# Cursor Terminal Configuration

## Problem: Terminal Detection Issues

Cursor sometimes doesn't detect when terminal commands have finished, leaving you waiting for a prompt that's already ready.

## Solutions

### 1. Check Terminal Settings

**Location**: Cursor Settings → Terminal

**Settings to Check**:
- **Terminal Integrated Shell Args**: Should be empty or minimal
- **Terminal Integrated Shell Windows**: Verify PowerShell path
- **Terminal Integrated Auto Replies**: May need configuration

### 2. PowerShell Prompt Configuration

The issue may be that PowerShell's prompt isn't being recognized. Try:

**Option A: Use a simpler prompt**
```powershell
# In PowerShell profile ($PROFILE)
function prompt {
    "PS $($PWD.Name)> "
}
```

**Option B: Ensure prompt ends with standard characters**
```powershell
# Default PowerShell prompt should end with "> " or "$ "
# If custom, ensure it ends with a space and recognizable character
```

### 3. Terminal Shell Configuration

**Check Cursor Settings**:
1. Open Settings (Ctrl+,)
2. Search for "terminal"
3. Look for:
   - `terminal.integrated.shell.windows`
   - `terminal.integrated.shellArgs.windows`
   - `terminal.integrated.automationProfile.windows`

**Recommended Configuration**:
```json
{
  "terminal.integrated.defaultProfile.windows": "PowerShell",
  "terminal.integrated.profiles.windows": {
    "PowerShell": {
      "source": "PowerShell",
      "args": []
    }
  },
  "terminal.integrated.automationProfile.windows": {
    "path": "powershell.exe",
    "args": ["-NoProfile"]
  }
}
```

### 4. Environment Variables

Some environment variables can affect prompt detection:

```powershell
# Check current prompt
$PROMPT

# Reset to default
$PROMPT = $null
```

### 5. Terminal Auto Replies

Cursor may need explicit prompt detection:

**Settings**:
```json
{
  "terminal.integrated.enablePersistentSessions": true,
  "terminal.integrated.persistentSessionReviveProcess": "onExit",
  "terminal.integrated.showExitAlert": false
}
```

### 6. Alternative: Use Command Prompt

If PowerShell continues to have issues, try Command Prompt:

```json
{
  "terminal.integrated.defaultProfile.windows": "Command Prompt",
  "terminal.integrated.profiles.windows": {
    "Command Prompt": {
      "path": "cmd.exe"
    }
  }
}
```

### 7. Manual Workaround

If automatic detection fails:
- Press Enter in terminal to "wake up" Cursor
- Use Ctrl+C to cancel if stuck
- Check terminal output manually

### 8. Check for Hanging Processes

Sometimes commands appear finished but have background processes:

```powershell
# Check for background jobs
Get-Job

# Check for running Python processes
Get-Process python -ErrorAction SilentlyContinue
```

### 9. Terminal Output Settings

**Settings that might help**:
```json
{
  "terminal.integrated.scrollback": 1000,
  "terminal.integrated.fastScrollSensitivity": 5,
  "terminal.integrated.mouseWheelScrollSensitivity": 3,
  "terminal.integrated.cursorBlinking": true,
  "terminal.integrated.cursorStyle": "line"
}
```

### 10. PowerShell Execution Policy

If commands are hanging, check execution policy:

```powershell
Get-ExecutionPolicy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Diagnostic Steps

1. **Test with simple command**:
   ```powershell
   echo "test"
   ```
   Does Cursor detect completion?

2. **Check terminal type**:
   ```powershell
   $PSVersionTable
   ```

3. **Test with different shell**:
   - Try Command Prompt
   - Try Git Bash (if installed)
   - Try WSL (if available)

4. **Check Cursor logs**:
   - Help → Toggle Developer Tools
   - Check Console for terminal-related errors

## Known Issues

- **PowerShell 7+**: May have different prompt behavior
- **Custom prompts**: Can confuse detection
- **Long-running commands**: May timeout detection
- **Background processes**: Can make terminal appear "busy"

## Recommended Configuration

For best compatibility with our Reverse Engineering Orchestrator:

```json
{
  "terminal.integrated.defaultProfile.windows": "PowerShell",
  "terminal.integrated.profiles.windows": {
    "PowerShell": {
      "source": "PowerShell",
      "args": ["-NoProfile", "-ExecutionPolicy", "Bypass"]
    }
  },
  "terminal.integrated.automationProfile.windows": {
    "path": "powershell.exe",
    "args": ["-NoProfile"]
  },
  "terminal.integrated.enablePersistentSessions": false,
  "terminal.integrated.showExitAlert": false
}
```

## Reporting Issues

If problems persist:
1. Check Cursor version (Help → About)
2. Check PowerShell version (`$PSVersionTable`)
3. Note any custom PowerShell profiles
4. Check for terminal extensions that might interfere

## References

- Cursor Settings: `File → Preferences → Settings`
- PowerShell Profile: `$PROFILE`
- Cursor Terminal Docs: Check Cursor documentation

