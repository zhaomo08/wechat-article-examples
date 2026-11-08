import os,subprocess,tempfile,json,platform
from pathlib import Path
ENV=os.environ|{'GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','GIT_AUTHOR_NAME':'Demo','GIT_AUTHOR_EMAIL':'demo@example.invalid','GIT_COMMITTER_NAME':'Demo','GIT_COMMITTER_EMAIL':'demo@example.invalid'}
def git(cwd,*args,check=True):
 p=subprocess.run(['git',*args],cwd=cwd,env=ENV,text=True,capture_output=True)
 if check and p.returncode: raise RuntimeError(p.stderr)
 return p
with tempfile.TemporaryDirectory(prefix='wechat-git-') as td:
 root=Path(td);remote=root/'remote.git';git(root,'init','--bare','--initial-branch=main',str(remote))
 git(root,'clone',str(remote),'seed');seed=root/'seed';(seed/'README.md').write_text('base\n');git(seed,'add','.');git(seed,'commit','-m','base');git(seed,'push','origin','main')
 for name in ['alice','bob']:git(root,'clone',str(remote),name)
 a,b=root/'alice',root/'bob'
 for p in [a,b]:(p/(p.name+'.txt')).write_text(p.name+'\n');git(p,'add','.');git(p,'commit','-m',p.name)
 assert git(a,'push','origin','main').returncode==0;rejected=git(b,'push','origin','main',check=False)
 assert rejected.returncode!=0 and 'rejected' in rejected.stderr
 print('同一分支：alice push=0；bob push=1（被拒绝）')
 git(b,'push','origin','HEAD:refs/heads/task/bob'); print('独立分支：bob 推到 task/bob=0')
 git(b,'fetch','origin');git(b,'rebase','origin/main');git(b,'push','origin','main')
 files=git(b,'ls-tree','--name-only','HEAD').stdout.splitlines();assert 'alice.txt' in files and 'bob.txt' in files
 print('先同步再整合：bob rebase + push=0；两份文件都保留')
 print('环境：'+platform.platform()+'；'+git(root,'--version').stdout.strip())
 print('范围：本地临时 bare 仓库，顺序模拟过期分支；没有访问 GitHub，没有压测 Rubicon。')
