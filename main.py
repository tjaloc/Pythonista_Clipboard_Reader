import ui
import clipboard
from time import sleep
from clipboard_reader import ClipboardReader



class ClipboardReaderApp:
    def __init__(self):
        self.cr = ClipboardReader()
        self.view = ui.load_view('clipboard_reader_ui.pyui')
        self.view.name = 'Clipboard Reader'
        self.view.present('sheet')
        
        self.read_loud()

    def read_loud(self):
        """Read text from the TextView."""
        content = clipboard.get()
        if not content:
            print('Nothing on clipboard. Copy some text.')
            
        elif not isinstance(content, str):
            print('No text to read on clipboard. Copy some text.')
        
        else:
        
            blocks = content.split('.')
            for block in blocks:
                while self.cr.is_speaking():
                    sleep(1)
                
                self.view['text_block'].text = block
                self.cr.read_loud(block)
                self.view['voice'].text = self.cr.who_is_speaking()
                
    def stop_speaking(self, sender):
        """Stop the speaking."""
        self.cr.stop_speaking()
        self.view.close()
        
if __name__ == '__main__':
    ClipboardReaderApp()

