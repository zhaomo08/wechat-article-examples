"""自造嵌套 ZIP 教学样本；不是元器导出格式解析器。只在临时目录运行。"""
import hashlib,io,json,tempfile,zipfile,platform
from pathlib import Path

def zip_bytes(files):
 out=io.BytesIO()
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  for name,data in files.items():z.writestr(name,data)
 return out.getvalue()

def inventory(data,prefix='',depth=0,budget=None):
 if budget is None:budget={'bytes':0,'entries':0}
 if depth>5:raise ValueError('教学样本超过递归深度限制')
 result={}
 with zipfile.ZipFile(io.BytesIO(data)) as z:
  if z.testzip() is not None:raise ValueError('ZIP CRC 校验失败')
  for entry in z.infolist():
   if entry.is_dir():continue
   budget['entries']+=1;budget['bytes']+=entry.file_size
   if budget['entries']>50 or budget['bytes']>2_000_000:raise ValueError('教学样本超过资源限制')
   raw=z.read(entry);name=prefix+entry.filename
   if entry.filename.endswith('.zip'):result.update(inventory(raw,name+'!/',depth+1,budget))
   else:result[name]={'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
 return result

def package(change=False,omit=False):
 config=json.dumps({'name':'演示助手','prompt':'新提示词' if change else '示例提示词'},ensure_ascii=False).encode()
 files={'app/config.json':config,'app/workflow.json':b'{"steps":["retrieve","answer"]}'}
 if not omit:files['app/faq.md']='这是自造知识文档，不含用户资料。'.encode()
 return zip_bytes({'metadata.json':b'{"sample":true}','apps.zip':zip_bytes({'demo.zip':zip_bytes(files)})})

with tempfile.TemporaryDirectory(prefix='wechat-backup-') as td:
 root=Path(td);baseline=inventory(package());(root/'baseline.json').write_text(json.dumps(baseline))
 expected=json.loads((root/'baseline.json').read_text())
 for label,raw,want_missing,want_changed in [('完整样本',package(),0,0),('缺文档样本',package(omit=True),1,0),('改配置样本',package(change=True),0,1)]:
  path=root/(label+'.zip');path.write_bytes(raw);actual=inventory(path.read_bytes())
  missing=sorted(set(expected)-set(actual));changed=sorted(k for k in set(expected)&set(actual) if expected[k]!=actual[k])
  assert (len(missing),len(changed))==(want_missing,want_changed)
  print(f'{label}：叶子文件 {len(actual)}，缺失 {len(missing)}，变化 {len(changed)}；ZIP CRC 均通过')
 print('环境：Python '+platform.python_version()+'；'+platform.system())
 print('范围：自造嵌套ZIP、外部可信基线；不是元器真实导出或迁移兼容性验证；不读取真实业务文件。')
