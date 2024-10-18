from objc_util import ObjCClass, ns
from preferences import VOICE_PREFERENCES, RATE

class ClipboardReader:

    def __init__(self):
        self.voices = None
        self.rate = RATE
        self.language = None
        self.name = None
        self.id = None
        
        self.NSLinguisticTagger = ObjCClass('NSLinguisticTagger')
        self.NSString = ObjCClass('NSString')
        self.AVSpeechSynthesisVoice = ObjCClass('AVSpeechSynthesisVoice')
        self.AVSpeechUtterance = ObjCClass('AVSpeechUtterance')
        self.AVSpeechSynthesizer = ObjCClass('AVSpeechSynthesizer')
        
        self.SYNTHESIZER = self.AVSpeechSynthesizer.alloc().init()
        self.UTTERANCE = None

    def who_is_speaking(self):
        return f'{self.name} ({self.language})'
        
    def detect_language(self, text: str) -> str:
        """Detect dominant language of a given Text.
        """
        string = self.NSString.stringWithString_(text)
        tagger = self.NSLinguisticTagger.alloc().initWithTagSchemes_options_(['Language'], 0)
        tagger.setString_(string)
        detected_language = tagger.dominantLanguage()
    
        return str(detected_language)
        
    def get_voices(self, lng: str) -> list:
        """Get available voices in a given language.
        """
        voices = self.AVSpeechSynthesisVoice.speechVoices()
        return [voice for voice in voices if str(voice.language()).startswith(lng)]
        
    
    def speak_with_voice(self, text, language_code, voice_identifier):
        """Replacement for speech.say() that also allows to choose a specific voice.
        """
        self.UTTERANCE = self.AVSpeechUtterance.alloc().initWithString_(ns(text))
        voice = self.AVSpeechSynthesisVoice.voiceWithIdentifier_(
            ns(voice_identifier))
        self.UTTERANCE.setVoice_(voice)
        self.UTTERANCE.setRate_(max(0, min(self.rate, 1))) # sets rate to 0 <= rate <= 1
        self.SYNTHESIZER.speakUtterance_(self.UTTERANCE)
    
    def read_loud(self, content: str) -> None:
        """ Read given text. The öanguage will be determined an a suitable voice will be picked.
        If a voice's name is in VOICE_PREFERENCES this voice will read the text. 
        """
        
        lng = self.detect_language(content)
        self.voices = self.get_voices(lng)
        
        
        for voice in self.voices:
            self.language = str(voice.language())
            self.name = str(voice.name())
            
            if self.name in VOICE_PREFERENCES:
                self.id = str(voice.identifier())
                break
        
        self.speak_with_voice(content, self.language, self.id)
        
        
    def pause_speaking(self):
        """Pause the speech synthesizer."""
        if self.is_speaking():
            self.SYNTHESIZER.pauseSpeakingAtBoundary_(0)  

    def resume_speaking(self):
        """Resume the speech synthesizer."""
        if not self.is_speaking():
            self.SYNTHESIZER.continueSpeaking()
        
    def is_speaking(self):
        return self.SYNTHESIZER.isSpeaking()
        
    def stop_speaking(self):
        """Stops the speech synthesizer if it is currently speaking."""
        if self.is_speaking():
            self.SYNTHESIZER.stopSpeakingAtBoundary_(0)  # 0 steht für AVSpeechBoundaryImmediate
            
