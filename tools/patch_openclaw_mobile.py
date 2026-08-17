from pathlib import Path
import re, sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('OpenClaw')

# 1) Browser-safe renderer + nonfatal audio fallback.
p=root/'OpenClaw/Engine/GameApp/BaseGameApp.cpp'
s=p.read_text()
old='''    uint32 rendererFlags = SDL_RENDERER_ACCELERATED;\n    if (gameOptions.useVerticalSync)\n    {\n        rendererFlags |= SDL_RENDERER_PRESENTVSYNC;\n    }\n\n    m_pRenderer = SDL_CreateRenderer(m_pWindow, -1, rendererFlags);\n    if (m_pRenderer == NULL)\n    {\n        LOG_ERROR("Failed to create SDL2 Renderer. Error: %s" + std::string(SDL_GetError()));\n        return false;\n    }\n'''
new='''#ifdef __EMSCRIPTEN__\n    // Android Chrome/content:// is substantially more reliable with SDL's software renderer.\n    // OpenClaw is a 2D sprite game, so this is also a good compatibility tradeoff.\n    uint32 rendererFlags = SDL_RENDERER_SOFTWARE;\n#else\n    uint32 rendererFlags = SDL_RENDERER_ACCELERATED;\n    if (gameOptions.useVerticalSync)\n    {\n        rendererFlags |= SDL_RENDERER_PRESENTVSYNC;\n    }\n#endif\n\n    m_pRenderer = SDL_CreateRenderer(m_pWindow, -1, rendererFlags);\n#ifdef __EMSCRIPTEN__\n    if (m_pRenderer == NULL)\n    {\n        LOG_WARNING("Software renderer failed, retrying default SDL renderer: " + std::string(SDL_GetError()));\n        m_pRenderer = SDL_CreateRenderer(m_pWindow, -1, 0);\n    }\n#endif\n    if (m_pRenderer == NULL)\n    {\n        LOG_ERROR("Failed to create SDL2 Renderer. Error: " + std::string(SDL_GetError()));\n        return false;\n    }\n'''
if old not in s: raise SystemExit('renderer block not found')
s=s.replace(old,new)
old='''    m_pAudio = new Audio();\n    if (!m_pAudio->Initialize(gameOptions))\n    {\n        LOG_ERROR("Failed to initialize SDL Mixer audio subsystem");\n        return false;\n    }\n\n    LOG("Audio successfully initialized.");\n'''
new='''    m_pAudio = new Audio();\n    if (!m_pAudio->Initialize(gameOptions))\n    {\n#ifdef __EMSCRIPTEN__\n        // WebAudio can remain suspended until a browser gesture. Do not make audio failure fatal.\n        LOG_WARNING("SDL Mixer audio is unavailable in this browser session; continuing without audio.");\n#else\n        LOG_ERROR("Failed to initialize SDL Mixer audio subsystem");\n        return false;\n#endif\n    }\n    else\n    {\n        LOG("Audio successfully initialized.");\n    }\n'''
if old not in s: raise SystemExit('audio block not found')
s=s.replace(old,new)
ready_old='''    m_IsRunning = true;\n\n    return true;\n}'''
ready_new='''    m_IsRunning = true;\n    LOG("OPENCLAW_BROWSER_GAME_READY");\n\n    return true;\n}'''
if ready_old not in s: raise SystemExit('ready marker insertion point not found')
s=s.replace(ready_old, ready_new, 1)
p.write_text(s)

# 2) Make all audio calls safe when WebAudio could not initialize.
p=root/'OpenClaw/Engine/Audio/Audio.cpp'
s=p.read_text()
repls={
'void Audio::PlayMusic(const char* musicData, size_t musicSize, bool looping)\n{':'void Audio::PlayMusic(const char* musicData, size_t musicSize, bool looping)\n{\n    if (!m_bIsAudioInitialized) return;',
'void Audio::PauseMusic()\n{':'void Audio::PauseMusic()\n{\n    if (!m_bIsAudioInitialized) return;',
'void Audio::ResumeMusic()\n{':'void Audio::ResumeMusic()\n{\n    if (!m_bIsAudioInitialized) return;',
'void Audio::StopMusic()\n{':'void Audio::StopMusic()\n{\n    if (!m_bIsAudioInitialized) return;',
'bool Audio::PlaySound(const char* soundData, size_t soundSize, const SoundProperties& soundProperties)\n{':'bool Audio::PlaySound(const char* soundData, size_t soundSize, const SoundProperties& soundProperties)\n{\n    if (!m_bIsAudioInitialized) return false;',
'bool Audio::PlaySound(Mix_Chunk* sound, const SoundProperties& soundProperties)\n{':'bool Audio::PlaySound(Mix_Chunk* sound, const SoundProperties& soundProperties)\n{\n    if (!m_bIsAudioInitialized) return false;',
'void Audio::StopAllSounds()\n{':'void Audio::StopAllSounds()\n{\n    if (!m_bIsAudioInitialized) return;',
'void Audio::PauseAllSounds()\n{':'void Audio::PauseAllSounds()\n{\n    if (!m_bIsAudioInitialized) return;',
'void Audio::ResumeAllSounds()\n{':'void Audio::ResumeAllSounds()\n{\n    if (!m_bIsAudioInitialized) return;',
}
for a,b in repls.items():
    if a not in s: raise SystemExit('audio method marker not found: '+a.splitlines()[0])
    s=s.replace(a,b,1)
s=s.replace('''    if (m_bSoundOn)\n    {\n        Mix_Volume(-1, m_SoundVolume);\n    }\n''','''    if (m_bSoundOn && m_bIsAudioInitialized)\n    {\n        Mix_Volume(-1, m_SoundVolume);\n    }\n''',1)
s=s.replace('''    if (active)\n    {\n        Mix_Resume(-1);\n        Mix_Volume(-1, m_SoundVolume);\n    }\n    else\n    {\n        Mix_Pause(-1);\n    }\n\n    m_bSoundOn = active; \n''','''    if (m_bIsAudioInitialized)\n    {\n        if (active)\n        {\n            Mix_Resume(-1);\n            Mix_Volume(-1, m_SoundVolume);\n        }\n        else\n        {\n            Mix_Pause(-1);\n        }\n    }\n\n    m_bSoundOn = active; \n''',1)
s=s.replace('''    if (active)\n    {\n        ResumeMusic();\n    }\n    else\n    {\n        PauseMusic();\n    }\n\n    m_bMusicOn = active; \n''','''    if (m_bIsAudioInitialized)\n    {\n        if (active)\n        {\n            ResumeMusic();\n        }\n        else\n        {\n            PauseMusic();\n        }\n    }\n\n    m_bMusicOn = active; \n''',1)
p.write_text(s)

# 3) Allow WASM heap growth instead of hard failure at 256 MiB.
p=root/'CMakeLists.txt'
s=p.read_text()
needle='-s TOTAL_MEMORY=268435456'
if needle not in s: raise SystemExit('TOTAL_MEMORY marker not found')
s=s.replace(needle, needle+' -s ALLOW_MEMORY_GROWTH=1',1)
p.write_text(s)

# 4) Phone-friendly display config and enable the source project's touch resolver.
p=root/'Build_Release/config.xml'
s=p.read_text()
s=re.sub(r'<Size width="\d+" height="\d+"\s*/>', '<Size width="960" height="540" />', s, count=1)
s=re.sub(r'<Scale>[^<]+</Scale>', '<Scale>1.0</Scale>', s, count=1)
if '<ControlOptions>' not in s:
    control='''  <ControlOptions>\n    <UseAlternateControls>false</UseAlternateControls>\n    <TouchScreen>\n      <Enable>true</Enable>\n      <DistanceThreshold>0.05</DistanceThreshold>\n      <TimeThreshold>100</TimeThreshold>\n    </TouchScreen>\n  </ControlOptions>\n'''
    s=s.replace('  <DebugOptions>', control+'  <DebugOptions>', 1)
p.write_text(s)

print('Applied OpenClaw mobile-web compatibility patch')
