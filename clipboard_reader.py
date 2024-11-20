import re
from objc_util import ObjCClass, ns, create_objc_class
from preferences import RATE, VOICE_PREFERENCES


class ClipboardReader:
    def __init__(self):
        self.voices = list(ObjCClass('AVSpeechSynthesisVoice').speechVoices())
        self.rate = RATE
        self.language = None
        self.name = None
        self.id = None
        self.current_text = ''
        self.busy = False
        
        self.SYNTHESIZER = ObjCClass('AVSpeechSynthesizer').alloc().init()
        self.UTTERANCE = None
        
        self.setup_delegate()
        
    def setup_delegate(self):
        """Helper to use ObjC's speech synthesizer's didFinish-method. When reader is finished reading its status changes to 'not busy'.
        
        Why not simply use self.SYNTHESIZER.isSpeaking()?
        The busy state includes preprocessing i.e. getting the dominant language and a voice.
        """
        
        def on_speech_finished():
            """Helper function to avoid ObjectC's Key Value Coding Error. Delegate doesn't support direct access to python attributes and throws an error ("this class is not key value coding-compliant for the key 'busy'").
            """
            self.busy = False
            
        def speechSynthesizer_didFinishSpeechUtterance_(_self, _cmd, synthesizer, utterance):
            on_speech_finished()
        
        DelegateClass = create_objc_class(
            'SpeechSynthDelegate',
            methods=[speechSynthesizer_didFinishSpeechUtterance_],
            protocols=['AVSpeechSynthesizerDelegate']
        )
        
        self.delegate = DelegateClass.alloc().init()
        
        try:
            self.SYNTHESIZER.setDelegate_(self.delegate)
        except Exception as e:
            print(f"Error setting delegate: {e}")
        
    def who_is_speaking(self):
        """Return name and language of current voice.
        """
        return f'{self.name} ({self.language})'
    
    def block_has_no_words(self, block: str):
        """Checks if the block contains no valid words.
        A valid word is defined as having at least two consecutive Unicode letters.
        """
        return not bool(re.search(r'[^\W\d_]{2,}', block))
        
    def detect_language(self, text: str) -> str:
        """Detect dominant language of a given Text.
        """
        
        # If text block includes no words objC cannot detect language. Use previously detected language or english as fallback.
        if self.block_has_no_words(text):
            fallback = self.language or 'en'
            return fallback
                
        string = ObjCClass('NSString').stringWithString_(text)
        tagger = ObjCClass('NSLinguisticTagger').alloc().initWithTagSchemes_options_(['Language'], 0)
        tagger.setString_(string)
        detected_language = tagger.dominantLanguage()
        lng = str(detected_language)
        
        return lng
        
    def speak_with_voice(self, text):
        """Replacement for speech.say() that also allows to choose a specific voice.
        """
        # change state
        self.busy = True 
        
        # create new UTTERANCE
        self.UTTERANCE = ObjCClass('AVSpeechUtterance').alloc().initWithString_(ns(text))
        self.current_text = str(self.UTTERANCE.valueForKey_("speechString"))
        
        # set params
        voice = ObjCClass('AVSpeechSynthesisVoice').voiceWithIdentifier_(
            ns(self.id))
        self.UTTERANCE.setVoice_(voice)
        self.update_speed_rate()
        
        # speak
        self.SYNTHESIZER.speakUtterance_(self.UTTERANCE)
        
    def read_loud(self, content: str) -> None:
        """ Read given text. The dominant language will be determined to pick a suitable voice.
        If a suitable voice's name is in VOICE_PREFERENCES this voice will read the text. 
        """
        self.busy = True
        lng = self.detect_language(content)
        
        for voice in self.voices:
            
            # filter by language
            language = str(voice.language()) 
            if not language.startswith(lng):
                continue
                
            self.name = str(voice.name())
            self.language = language
            self.id = str(voice.identifier())  
            
            # stop at first voice preference
            if self.name in VOICE_PREFERENCES:
                break
                
        self.speak_with_voice(content)
        
    def is_speaking(self):
        return self.SYNTHESIZER.isSpeaking()
        
    def stop_speaking(self):
        """Stops the speech synthesizer if it is currently speaking.
        """
        if self.is_speaking():
            self.SYNTHESIZER.stopSpeakingAtBoundary_(0)  # 0 steht für AVSpeechBoundaryImmediate
            
    def update_speed_rate(self):
        """Set voices speed to self.rate, a value from 0 to 1.
        Updates apply to the next block.
        """
        self.UTTERANCE.setRate_(max(0, min(self.rate, 1)))
        
