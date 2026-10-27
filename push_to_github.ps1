cd $PSScriptRoot
git init -b main
git add .gitignore README.md hero_blockout_v01_final_v5.blend hero_blockout_v01_final_v7.blend
git commit -m "Hero blockout v1: final_v5 (60fps baseline) + final_v7 (processing pass, white-model)"
$remote = Read-Host "粘贴 GitHub 空仓库地址 (形如 https://github.com/xxx/yyy.git)，直接回车跳过"
if ($remote) {
  git remote add origin $remote
  git push -u origin main
} else {
  Write-Host "已在本地提交。如需推送，去 github.com 建空仓库后再跑: git remote add origin <地址>; git push -u origin main"
}
