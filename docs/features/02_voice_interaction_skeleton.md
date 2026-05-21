# Feature 02: Voice Interaction Skeleton

## Implemented

- Real microphone-listen path for macOS through `voice listen`
- Built-in openWakeWord `Hey Mycroft` activation
- Silence-bounded local utterance capture
- Local Whisper STT adapter
- Transcript routing into `ChatService` with conversation ID preservation
- macOS `say` TTS output
- Post-reply active listening window for wake-free follow-up speech
- Transcript CLI fallback through `voice transcript <text>`

## Limitations

Voice setup depends on local audio permissions, installed voice dependencies,
downloaded wake-word model assets when required, and a local Whisper model cache.
Commands, RAG, screen context, gestures, cloud speech, and app integrations stay
outside this phase.
