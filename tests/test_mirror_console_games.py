import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import mirror_console_games as m
class CatalogTests(unittest.TestCase):
 def setUp(self):self.data=json.loads(Path('consoles/catalog.json').read_text())
 def test_exact_snapshot(self):self.assertEqual(len(m.records(self.data)),5)
 def test_hash_change_refused(self):
  self.data['records'][0]['sha256']='0'*64
  with self.assertRaises(ValueError):m.records(self.data)
 def test_new_game_refused(self):
  self.data['records'][0]['file']='Private-Fable.zip'
  with self.assertRaises(ValueError):m.records(self.data)
 def test_owner_only_path_refused(self):
  self.data['records'][0]['url']='/downloads/n64-texture-packs/private.zip'
  with self.assertRaises(ValueError):m.records(self.data)
 def test_missing_refused(self):
  self.data['records'].pop()
  with self.assertRaises(ValueError):m.records(self.data)
 def test_duplicate_refused(self):
  self.data['records'].append(self.data['records'][0])
  with self.assertRaises(ValueError):m.records(self.data)
 def test_duplicate_tag_refused(self):
  self.data['records'][1]['tag']=self.data['records'][0]['tag']
  with self.assertRaises(ValueError):m.records(self.data)

 def test_unapproved_wip_refused(self):
  self.data['records'][-1]['url']='/downloads/xbox-360/wip/unreviewed.exe'
  with self.assertRaises(ValueError):m.records(self.data)
 def test_fable_identity_refused(self):
  self.data['records'][-1]['sha256']='0'*64
  with self.assertRaises(ValueError):m.records(self.data)
