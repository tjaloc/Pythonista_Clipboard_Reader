from objc_util import ObjCClass, ns, create_objc_class#, ObjCInstance
from preferences import RATE, VOICE_PREFERENCES

class ClipboardReader:
    def __init__(self):
        self.voices = None
        self.rate = RATE
        self.language = None
        self.name = None
        self.id = None
        self.current_text = ''
        
        self.SYNTHESIZER = ObjCClass('AVSpeechSynthesizer').alloc().init()
        self.UTTERANCE = None
        
        self.busy = False
        self.setup_delegate()
        
    def setup_delegate(self):
        """Helper to use ObjC's speech synthesizer's didFinish-method. When reader is finished reading its status changes to 'not busy'.
        
        Why not simply use self.SYNTHESIZER.isSpeaking()?
        
        The busy state includes preprocessing i.e. getting the dominant language and a voice.
        """
        reader = self
        def speechSynthesizer_didFinishSpeechUtterance_(_self, _cmd, synthesizer, utterance):
            reader.busy = False
        
        DelegateClass = create_objc_class(
            'SpeechSynthDelegate',
            methods=[speechSynthesizer_didFinishSpeechUtterance_],
            protocols=['AVSpeechSynthesizerDelegate']
        )
        self.delegate = DelegateClass.alloc().init()
        self.SYNTHESIZER.setDelegate_(self.delegate)
        
    def who_is_speaking(self):
        """Return name and language of current voice.
        """
        return f'{self.name} ({self.language})'
        
    def detect_language(self, text: str) -> str:
        """Detect dominant language of a given Text.
        """
        string = ObjCClass('NSString').stringWithString_(text)
        tagger = ObjCClass('NSLinguisticTagger').alloc().initWithTagSchemes_options_(['Language'], 0)
        tagger.setString_(string)
        detected_language = tagger.dominantLanguage()
    
        return str(detected_language)
        
    def get_voices(self, lng: str) -> list:
        """Get available voices in a given language.
        """
        voices = ObjCClass('AVSpeechSynthesisVoice').speechVoices()
        return [voice for voice in voices if str(voice.language()).startswith(lng)]
        
    def speak_with_voice(self, text):
        """Replacement for speech.say() that also allows to choose a specific voice.
        """
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
        self.voices = self.get_voices(lng)
        
        for voice in self.voices:
            self.language = str(voice.language())
            self.name = str(voice.name())
            
            if self.name in VOICE_PREFERENCES:
                self.id = str(voice.identifier())
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
        
