# 修复乱码的 commit message
# 使用 git rebase 来修改

# 获取需要修改的 commit SHA
$commits = @(
    @{sha="d38404b"; msg="feat: Add multi-sources testing functionality and documentation"},
    @{sha="f6e870e"; msg="feat: Complete all core features in TODO.md"},
    @{sha="cf2cdec"; msg="feat: Add visual configuration management panel"}
)

# 从最旧的开始修改
foreach ($commit in $commits) {
    Write-Host "Fixing commit $($commit.sha)..."
    # 使用 git rebase 来修改
    $env:GIT_SEQUENCE_EDITOR = "powershell -Command `"`$content = Get-Content `$args[0]; `$content = `$content -replace '^pick $($commit.sha)', 'reword $($commit.sha)'; Set-Content `$args[0] `$content`""
    git rebase -i "$($commit.sha)^"
    
    # 修改 commit message
    git commit --amend -m "$($commit.msg)"
    
    # 继续 rebase
    git rebase --continue
}

Write-Host "Done!"

