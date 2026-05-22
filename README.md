# LocalMacAgent

LocalMacAgent is a local-first, voice-first, chat-native assistant project for macOS.
Phase 0 provides the repository foundation. Phase 1 adds a local text chat loop
with persisted JSONL conversation history, compact core-memory context, and a
real local Ollama backend by default.

Future phases will add commands, RAG, memory routing, screen context, app
integrations, optional cloud-safe workflows, and a Swift native shell. Those
features are documented but not implemented yet.

## Development

Use Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
./scripts/run_tests.sh
./scripts/run_dev.sh
```

The development CLI accepts plain typed messages plus `help`,
`voice transcript <text>`, `classify <action>`, and `exit`.

```text
> hello
<local Ollama model response>
Latency chat | store_user: ... ms | build_context: ... ms | llm: ... ms | total: ... ms
```

Configuration defaults live in `configs/`; local overrides can be placed in `.env`.
The default model config uses Ollama at `http://127.0.0.1:11434` with `gemma3`.
Start Ollama and pull the configured local model before using chat, or set
`LOCAL_MAC_AGENT_MODEL__MODEL_NAME` in `.env` to another local Ollama model.
If Ollama is unavailable, chat reports that no LLM is configured instead of
generating a synthetic reply.

Voice transcript routing speaks the chat response through macOS TTS:

```text
> voice transcript summarize my notes
```

Wake listening starts with the CLI. Say `Hey Mycroft` to use the microphone,
openWakeWord, local WebRTC VAD utterance detection, and local Whisper STT. Typed
text and spoken turns share the same default conversation context, so they can be
mixed freely. Install the voice dependencies, allow microphone access for the
terminal or app running LocalMacAgent, make the local Whisper model available,
download the openWakeWord built-in models when needed, and keep Ollama running
for chat responses:

```bash
python -c "import openwakeword; openwakeword.utils.download_models(['hey_mycroft'])"
```

openWakeWord's included pretrained models have separate model-license terms;
review them before redistribution.

Voice defaults to Whisper `tiny.en` and a short trailing-silence cutoff for
lower latency. Override `LOCAL_MAC_AGENT_VOICE__WHISPER_MODEL` for a larger model
when accuracy matters more than response speed.
Each completed typed or spoken request prints a local latency breakdown. Typed
chat isolates persistence, context build, model response, event logging, and
context-delta writes. Voice transcript mode adds TTS; live microphone turns also
show utterance capture and STT time.
WebRTC VAD mode defaults to `2`; tune `LOCAL_MAC_AGENT_VOICE__VAD_MODE` between
`0` and `3` if your microphone environment cuts off speech or accepts too much
non-speech.
