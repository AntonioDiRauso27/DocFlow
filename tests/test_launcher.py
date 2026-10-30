import io,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
class LauncherTests(unittest.TestCase):
 def test_posix_detach(self):
  with patch.object(server.os,'name','posix'),patch.object(server.subprocess,'Popen') as popen:
   server.spawn_server(['python','server.py','--serve'],io.BytesIO())
   options=popen.call_args.kwargs;self.assertTrue(options['start_new_session']);self.assertNotIn('creationflags',options);self.assertEqual(options['stdin'],server.subprocess.DEVNULL)
 def test_windows_no_console(self):
  with patch.object(server.os,'name','nt'),patch.object(server.subprocess,'CREATE_NO_WINDOW',0x08000000,create=True),patch.object(server.subprocess,'CREATE_NEW_PROCESS_GROUP',0x200,create=True),patch.object(server.subprocess,'Popen') as popen:
   server.spawn_server(['pythonw.exe','server.py','--serve'],io.BytesIO())
   options=popen.call_args.kwargs;self.assertEqual(options['creationflags'],0x08000200);self.assertNotIn('start_new_session',options);self.assertTrue(options['close_fds'])
if __name__=='__main__':unittest.main()
