# 修复乱码的 commit message
# 使用 git rebase 来修改

# 修改 d38404b
git rebase -i d38404b^
# 在编辑器中，将 pick 改为 reword，然后修改 commit message

# 修改 f6e870e  
git rebase -i f6e870e^
# 在编辑器中，将 pick 改为 reword，然后修改 commit message

# 修改 cf2cdec
git rebase -i cf2cdec^
# 在编辑器中，将 pick 改为 reword，然后修改 commit message

