function Show-DirectoryTree {
    param (
        [string]$Path = ".",
        [string]$Indent = "",
        [string]$IgnoreDirRegex = '^(node_modules|\.next|out|build|dist|venv|\.venv|env|temp|img|images|__pycache__|site-packages|\.DS_Store|Thumbs\.db|\.vscode|\.idea|\.git)$',
        [string]$IgnoreFileRegex = '\.(py[cod]|pyo|db|sqlite|log|env|pkl|swp|env\.local|env\.development\.local|env\.test\.local|env\.production\.local)$|Pipfile\.lock$'
    )

    $items = Get-ChildItem -Path $Path -Force  # Get all items (dirs + files), including hidden
    foreach ($item in $items) {
        if ($item.PSIsContainer) {
            if ($item.Name -match $IgnoreDirRegex) { continue }
            Write-Output "$Indent+--- [$($item.Name)]"  # Directory marked with []
            Show-DirectoryTree -Path $item.FullName -Indent "$Indent|   " -IgnoreDirRegex $IgnoreDirRegex -IgnoreFileRegex $IgnoreFileRegex
        } else {
            if ($item.Name -match $IgnoreFileRegex) { continue }
            Write-Output "$Indent+--- $($item.Name)"  # File plain
        }
    }
}

Show-DirectoryTree > map.txt