"""Mirror only the checksum-pinned public console game packages; never execute them."""
import argparse,hashlib,json,re,tempfile,urllib.parse,urllib.request,zipfile
from pathlib import Path,PurePosixPath
from mirror_games import release_index,mutate_json
ORIGIN='https://retroremakes.retroremakes.chatgpt.site'
EXPECTED={
'fable-iii-c92e3527-setup-0-1-1.exe':('xbox-360',34040832,'0b834a4d1788669b2e4c05aa7dda0a6eba7c76d82d08637aad320f89f708c3ce'),
'Gears2-OwnCopy-Setup-0.1.0-rc2.exe':('xbox-360',226864500,'f35b2233fd2b20691206dbc2a92041280bc6b563dece27523e3ce881d6c8eba0'),
'Gears2-Mods-Companion-v0.1.0.zip':('xbox-360',13484,'473b9d58fc313018f9891752120065949ad5a2c13e964ff7376a3ec110d3c0e0'),
'RetroRemakes-Rush2049-Mods-v0.3.4-Update.exe':('n64',6550528,'8b35bb62c9b5660afd106cc66f32cc1ea00d3925d913e7f893420799a2ac9295'),
'Rush2049-Launcher-Mods-v0.3.4-Source.zip':('n64',166418,'43132db1ef4e1f97a4b23cc295b28e99eb68bb490434308df6d2428dc09760f1')}
def records(data):
 rows=data['records'];seen=set()
 for r in rows:
  file=r['file'];actual=(r['console'],r['bytes'],r['sha256'])
  if file not in EXPECTED or actual!=EXPECTED[file] or file in seen:raise ValueError('Not an exact approved public game download')
  expected='/downloads/xbox-360/wip/'+file if file=='fable-iii-c92e3527-setup-0-1-1.exe' else ('/downloads/xbox-360/v0.1.0-rc2/'+file if file.startswith('Gears2-OwnCopy') else '/assets/game-mods/'+file)
  if r['url']!=expected or not re.fullmatch(r'[a-z0-9.-]+',r['tag']):raise ValueError('Unexpected path or release tag')
  seen.add(file)
 if seen!=set(EXPECTED):raise ValueError('Incomplete public game snapshot')
 if len({r['tag'] for r in rows})!=len(rows):raise ValueError('Duplicate tag')
 return rows

def validate(path):
 if path.suffix=='.exe':
  with path.open('rb') as f:
   if f.read(2)!=b'MZ':raise ValueError('Expected PE installer')
  return
 with zipfile.ZipFile(path) as z:
  seen=set()
  for i in z.infolist():
   n=i.filename.rstrip('/');p=PurePosixPath(n)
   if not n or p.is_absolute() or '..' in p.parts or '\\' in n or ':' in n or n.casefold() in seen or (i.external_attr>>16)&0o170000==0o120000:raise ValueError('Unsafe ZIP')
   seen.add(n.casefold())
   if p.suffix.lower() in {'.iso','.z64','.v64','.n64','.xex','.chd','.cue','.mcd','.mcr','.mpk','.sav'}:raise ValueError('Game image or player data in ZIP')
  if z.testzip():raise ValueError('ZIP CRC mismatch')

def download(r,path):
 h=hashlib.sha256();count=0;url=ORIGIN+r['url']
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'RetroRemakes-Console-Game-Mirror/1'}),timeout=120) as response,path.open('wb') as out:
  if response.url!=url:raise ValueError('Unexpected redirect')
  while b:=response.read(1024*1024):
   count+=len(b)
   if count>r['bytes']:raise ValueError('Oversized download')
   h.update(b);out.write(b)
 if count!=r['bytes'] or h.hexdigest()!=r['sha256']:raise ValueError('Website bytes mismatch')
 validate(path)

def main():
 p=argparse.ArgumentParser();p.add_argument('catalog',type=Path);p.add_argument('--repo',required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 if a.repo!='RemakerGamee/ps1-remaker-public':raise ValueError('Unexpected repository')
 rows=records(json.loads(a.catalog.read_text()));releases=release_index(a.repo);results=[]
 def save(status):a.report.write_text(json.dumps({'status':status,'expected_assets':len(rows),'verified_assets':len(results),'complete':len(results)==len(rows),'results':results},indent=2)+'\n')
 save('in_progress')
 with tempfile.TemporaryDirectory(prefix='console-games-') as temp:
  temp=Path(temp)
  for r in rows:
   release=releases.get(r['tag']);asset=None;payload=temp/'payload.json';local=temp/r['file']
   if release:
    if any(x['name']!=r['file'] for x in release['assets']):raise ValueError('Unexpected release asset')
    asset=next((x for x in release['assets'] if x['name']==r['file']),None)
    if asset and (asset['size']!=r['bytes'] or asset.get('digest')!='sha256:'+r['sha256']):raise ValueError('Existing asset differs')
   reused=asset is not None
   if not asset:
    download(r,local)
    if release is None:
     body=r['notes']+'\n\nMirrors the existing public website package without modifications. Original licenses and limitations apply. No game, installer or runtime was executed by this mirror.\n\nSHA256: `'+r['sha256']+'`\nBytes: '+str(r['bytes'])+'\nOriginal: '+ORIGIN+r['url']
     release=mutate_json('repos/'+a.repo+'/releases','POST',payload,{'tag_name':r['tag'],'name':r['title'],'body':body,'draft':True,'prerelease':True})
    endpoint='https://uploads.github.com/repos/'+a.repo+'/releases/'+str(release['id'])+'/assets?name='+urllib.parse.quote(r['file'],safe='')
    asset=mutate_json(endpoint,'POST',local,content_type='application/zip' if local.suffix=='.zip' else 'application/octet-stream')
    if asset['size']!=r['bytes'] or asset.get('digest')!='sha256:'+r['sha256']:raise ValueError('Uploaded asset differs')
    local.unlink()
   if release['draft']:release=mutate_json('repos/'+a.repo+'/releases/'+str(release['id']),'PATCH',payload,{'draft':False,'make_latest':'false'})
   results.append(dict(file=r['file'],console=r['console'],bytes=r['bytes'],sha256=r['sha256'],github_digest=asset['digest'],download_url=asset['browser_download_url'],release_url=release['html_url'],reused=reused))
   save('passed' if len(results)==len(rows) else 'in_progress');print('Verified',r['file'],flush=True)
if __name__=='__main__':main()
