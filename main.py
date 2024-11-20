import re
import ui
import clipboard

from clipboard_reader import ClipboardReader


class ClipboardReaderApp:
    def __init__(self):
        self.cr = ClipboardReader()
        self.view = ui.load_view('clipboard_reader_ui.pyui')
        self.view.name = 'Clipboard Reader'
        self.view.present('sheet')
        self.blocks = []
        self.btn_alpha = (1, 0.5)
        
    def faster(self, sender):
        self.cr.rate = min(1, self.cr.rate + 1/100)
        self.view['btn_fast'].alpha = self.btn_alpha[self.cr.rate == 1]
        self.cr.update_speed_rate()
        
    def slower(self, sender):
        self.cr.rate = max(0, self.cr.rate - 1/100)
        self.view['btn_fast'].alpha = self.btn_alpha[self.cr.rate == 0]
        self.cr.update_speed_rate()
        
    def read_clipboard(self, sender=None):
        if self.get_text_from_clipboard():
            self.read_next_block()
        
    def read_next_block(self):
        """Recursively reads all blocks. 
        
            Why not a for-loop?
            ui only updates once after the function is finished. With recursion it updates with every block. With a for-loop view'd update after the last block
        """
        if self.blocks == []:
            # case: nothing to read
            return
            
        if not self.cr.busy:
            # case: ready to read 
            self.current_block = self.blocks.pop(0)
            self.cr.read_loud(self.current_block)
            self.display_speaker()
            self.display_block()
        
        # wait and retry
        ui.delay(self.read_next_block, 1)
        
    def display_block(self):
        """Update Text View element with current text from clipboard reader.
        """
        self.view['text_block'].text = self.cr.current_text
        
    def display_speaker(self):
        """Update Label element with current voice's name and language from clipboard reader.
        """
        self.view['voice'].text = self.cr.who_is_speaking()
        
    def get_text_from_clipboard(self) -> bool:
        """Fetch text string from clipboard. Split into sentences, save as list in self.blocks and return True.
        """
        self.blocks = []
        content = clipboard.get()
        
        if not content:
            msg = 'Clipboard is empty. Copy some text to read.'
        elif not isinstance(content, str):
            msg = 'No text to read on clipboard. Copy some text.'
        else:
            blocks = re.split(r'(?:\n\s*\n|(?<=[.!?]) +|\n+)', content) # incl. whitespace/linebreaks
            self.blocks = [self.clear_block(block) for block in blocks if block.strip()]
            return True
            
        print(msg) 
        self.view['text_block'].text = msg 
        return False
        
    def clear_block(self, block):
        """Clean up clipboard strings:
            - Remove word splits caused by line breaks
            - Remove footnote numbers appearing at the end of sentences.
              (Note: Line breaks in the clipboard are replaced by spaces.)
        """ 
        # fuse split words 
        block = re.sub('-\s', '', block) 
        
        # remove footnote numbers 
        block = re.sub(r'\.(\d+)(\s|$)', r'.\2', block) 
        
        return block

    def stop_speaking(self, sender):
        """Stop the speaking.
        """
        if self.cr.is_speaking():
            self.cr.stop_speaking()
        
if __name__ == '__main__':
    app = ClipboardReaderApp()
    app.read_clipboard()
