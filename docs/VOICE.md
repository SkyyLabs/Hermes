# Voice

Phase 2 provides the local voice interaction path for macOS. `voice listen`
opens the microphone, waits for openWakeWord `Hey Mycroft`, captures an utterance
until trailing silence, transcribes the captured audio with local Whisper, routes
the transcript through `ChatService`, and speaks the assistant reply through the
macOS `say` command.

After a spoken reply, the conversation remains active for a short configurable
silence window. Follow-up speech inside that window is transcribed without
requiring another wake phrase. When that window expires, the listener returns to
waiting for `Hey Mycroft`.

`voice transcript <text>` bypasses microphone capture, wake detection, and STT,
but it still routes through the same voice service and performs TTS. That keeps a
manual fallback for transcript routing and deterministic verification.

## Boundaries

- Microphone capture uses `sounddevice` and requires macOS microphone permission.
- Wake detection uses openWakeWord's built-in `hey_mycroft` model.
- The macOS listener uses openWakeWord ONNX model assets. Download the built-in
  `hey_mycroft` assets with
  `python -c "import openwakeword; openwakeword.utils.download_models(['hey_mycroft'])"`
  if they are not already present.
- STT uses local Whisper and may download a configured model if it is not already
  available in the local runtime cache.
- TTS uses macOS `say`.
- Chat replies remain local through the configured `ChatService` model backend.

openWakeWord's included pretrained models carry their own model-license terms.
Voice does not implement commands, RAG, screen context, app integrations, or
cloud speech APIs in this phase.
